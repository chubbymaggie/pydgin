#=======================================================================
# sim.py
#=======================================================================
# This is the common top-level simulator. ISA implementations can use
# various hooks to configure the behavior.

import os
import sys

# ensure we know where the pypy source code is
# XXX: removed the dependency to PYDGIN_PYPY_SRC_DIR because rpython
# libraries are much slower than native python when running on an
# interpreter. So unless the user have added rpython source to their
# PYTHONPATH, we should use native python.
#try:
#  sys.path.append( os.environ['PYDGIN_PYPY_SRC_DIR'] )
#except KeyError as e:
#  print "NOTE: PYDGIN_PYPY_SRC_DIR not defined, using pure python " \
#        "implementation"

from pydgin.debug import Debug, pad, pad_hex
from pydgin.misc  import FatalError
from pydgin.jit   import JitDriver, hint, set_user_param, set_param, \
                         elidable

from pydgin.utils import cvt_int2bytes

from pydgin.misc_tpa import colors
from pydgin.misc_tpa import MemCoalescer
from pydgin.misc_tpa import LLFUAllocator
from pydgin.misc_tpa import ReconvergenceManager
from pydgin.misc_tpa import ThreadSelect
from pydgin.misc_tpa import MemRequest
from pydgin.misc_tpa import OperandsStruct

def jitpolicy(driver):
  from rpython.jit.codewriter.policy import JitPolicy
  return JitPolicy()

#-------------------------------------------------------------------------
# Sim
#-------------------------------------------------------------------------
# Abstract simulator class

class Sim( object ):

  def __init__( self, arch_name, jit_enabled=False ):

    self.arch_name   = arch_name

    self.jit_enabled = jit_enabled

    if jit_enabled:
      self.jitdriver = JitDriver( greens =['pc', 'core_id'],
                                  reds   = ['max_insts', 'state', 'sim',],
                                  #virtualizables  =['state',],
                                  get_printable_location=self.get_location,
                                )

      # Set the default trace limit here. Different ISAs can override this
      # value if necessary
      self.default_trace_limit = 400000

    self.max_insts = 0
    self.max_ticks = 0
    self.tick_ctr = 0

    self.ncores = 1
    self.core_switch_ival = 1
    self.pkernel_bin = None

    # shreesha: adding extra stuff here
    self.reconvergence_manager = ReconvergenceManager()
    self.dmem_coalescer        = MemCoalescer()
    self.mdu_allocator         = LLFUAllocator()
    self.fpu_allocator         = LLFUAllocator(False)

    # shreesha: adding extra stuff here
    self.reconvergence      = 0
    self.active_cores       = 0
    self.inst_ports         = 0     # Instruction bandwidth
    self.data_ports         = 0     # Data bandwidth
    self.mdu_ports          = 0     # MDU bandwidth
    self.fpu_ports          = 0     # FPU bandwidth
    self.icache_line_sz     = 0     # Insn cache line size (default word size)
    self.dcache_line_sz     = 0     # Data cache line size (set based on num cores)
    self.l0_buffer_sz       = 0     # L0 buffer size
    self.linetrace          = False
    self.color              = False
    self.barrier_limit      = 250   # barrier hint limit
    self.barrier_delta      = 0     # barrier delta limits
    self.barrier_hits       = 0     # barrier success
    self.barrier_miss       = 0     # barrier miss
    self.num_tasks          = 0     # number of tasks executed
    self.adaptive_hint      = False # turn on adaptive barrier limits
    self.icoalesce          = True  # toggle instruction coalescing
    self.iword_match        = True  # toggle instruction word vs. line matching
    self.simt               = False # toggle to indicate simt frontend
    self.simt_l0_buffer     = []    # global simt L0 buffer
    self.sched_limit        = 0     # max cycles for priority thread selection
    self.lockstep           = 0     # lockstep see options
    self.task_lockstep      = False # used in lockstep
    self.limit_lockstep     = False # set the max lockstep group size to resources
    self.mt                 = False # toggle to indicate MT mode

    # stats
    # NOTE: Collect the stats below only when in parallel mode
    self.unique_insts         = 0 # unique insts in parallel regions
    self.unique_spmd          = 0 # unique insts in spmd region
    self.unique_task          = 0 # unique insts in wsrt tasks
    self.unique_runtime       = 0 # unique insts in wsrt runtime
    self.unique_imem_accesses = 0 # unique number of imem accesses
    self.unique_dmem_accesses = 0 # unique number of dmem accesses
    self.total_spmd           = 0 # total insts in spmd region
    self.total_task           = 0 # total insts in wsrt tasks
    self.total_runtime        = 0 # total insts in wsrt runtime
    self.total_wsrt           = 0 # total insts in wsrt region
    self.total_parallel       = 0 # total number of instructions in parallel regions
    self.total_imem_accesses  = 0 # total number of imem accesses
    self.total_dmem_accesses  = 0 # total number of dmem accesses
    self.total_coalesces      = 0 # total number of instruction coalesces
    self.simt_l0_hits         = 0 # total hits in simt l0 buffer

    self.total_executes       = 0 # Total instructions that produce a value
    self.unique_executes      = 0 # Unique instructions that produce a value

    self.total_frontend       = 0 # Total frontend usage
    self.unique_frontend      = 0 # Unique frontend usage

    # NOTE: Total number of instructions in timing loop
    self.total_steps     = 0
    self.serial_steps    = 0

    self.task_queue = []

    # output file
    self.outfile = ''

  #-----------------------------------------------------------------------
  # decode
  #-----------------------------------------------------------------------
  # This needs to be implemented in the child class

  def decode( self, bits ):
    raise NotImplementedError()

  #-----------------------------------------------------------------------
  # init_state
  #-----------------------------------------------------------------------
  # This needs to be implemented in the child class

  def init_state( self, exe_file, exe_name, run_argv, testbin ):
    raise NotImplementedError()

  #-----------------------------------------------------------------------
  # help message
  #-----------------------------------------------------------------------
  # the help message to display on --help

  help_message = """
  Pydgin %s Instruction Set Simulator
  usage: %s <args> <sim_exe> <sim_args>

  <sim_exe>  the executable to be simulated
  <sim_args> arguments to be passed to the simulated executable
  <args>     the following optional arguments are supported:

    --help,-h       Show this message and exit
    --test          Run in testing mode (for running asm tests)
    --env,-e <NAME>=<VALUE>
                    Set an environment variable to be passed to the
                    simulated program. Can use multiple --env flags to set
                    multiple environment variables.
    --debug,-d <flags>[:<start_after>]
                    Enable debug flags in a comma-separated form (e.g.
                    "--debug syscalls,insts"). If provided, debugs starts
                    after <start_after> cycles. The following flags are
                    supported:
         insts              cycle-by-cycle instructions
         rf                 register file accesses
         mem                memory accesses
         regdump            register dump
         syscalls           syscall information
         bootstrap          initial stack and register state

    --max-insts <i> Run until the maximum number of instructions
    --max-ticks <i> Run until the maximum number of ticks in stats region
    --ncores <i>    Number of cores to simulate
    --core-switch-ival <i>
                    Switch cores at this interval
    --pkernel <f>   Load pkernel binary
    --jit <flags>   Set flags to tune the JIT (see
                    rpython.rlib.jit.PARAMETER_DOCS)
    --linetrace     Turn on linetrace for parallel mode
    --color         Turn on color for linetraces
    --analysis      Use the options below
        0 No reconvergence
        1 Min-pc, round-robin
        2 Min-sp/pc, round-robin
    --runtime-md    Runtime metadata used in analysis
    --inst-ports    Number of instruction ports (bandwidth)
    --data-ports    Number of data ports (bandwidth)
    --mdu-ports     Number of MDU ports (bandwidth)
    --fpu-ports     Number of FPU ports (bandwidth)
    --lockstep      Enforce lockstep execution on mem/llfu divergence
        0             No lockstep execution (default)
        1             Lockstep execution
        2             Task-aware lock-step execution
    --icache-line-sz  Cache line size in bytes
    --dcache-line-sz  Cache line size in bytes
    --l0-buffer-sz    L0 buffer size in icache-line-sz
    --adaptive-hint   Turn on for adaptive hints
    --barrier-delta   Default 50
    --barrier-limit   Max stall cycles for barrier limit
    --icoalesce       Toggle coalescing for instructions (default True)
    --iword-match     Toggle instruction word vs. line matching (default word)
    --simt            Toggle for SIMT frontend (default False)
                      Really means shared frontend or not
    --sched-limit     Limit for scheduling to guarantee forward progress
    --outfile         Name for the output trace dump
    --limit-lockstep  Limit the max group size to resources for lockstep execution
    --mt              Multithread-mode (runs a different loop)
  """

  #-----------------------------------------------------------------------
  # get_location
  #-----------------------------------------------------------------------
  # for debug printing in PYPYLOG

  @staticmethod
  def get_location( pc, core_id ):
    # TODO: add the disassembly of the instruction here as well
    return "pc: %x core_id: %x" % ( pc, core_id )

  @elidable
  def next_core_id( self, core_id ):
    return ( core_id + 1 ) % self.ncores

  #-----------------------------------------------------------------------
  # run_mt
  #-----------------------------------------------------------------------
  # NOTE: MT mode should always run with one instruction port

  def run_mt( self ):

    max_insts = self.max_insts
    max_ticks = self.max_ticks
    core_id   = 0
    pre_execute_pc = 0

    l0_mask = ~(self.icache_line_sz - 1) & 0xFFFFFFFF
    dmem_mask = ~(self.dcache_line_sz - 1) & 0xFFFFFFFF

    last_active_pc = 0
    last_mem_req   = MemRequest()
    last_operands  = OperandsStruct()

    thread_select = ThreadSelect( self.ncores, self.sched_limit )

    while self.states[0].running:
      # check if we have reached the end of the maximum instructions and
      # exit if necessary
      if max_insts != 0 and self.states[0].num_insts >= max_insts:
        print "Reached the max_insts (%d), exiting." % max_insts
        break

      # check if we have reached the end of the maximum ticks and exit if
      # necessary
      if max_ticks != 0 and self.tick_ctr >= max_ticks:
        print "Reached the max_ticks (%d), exiting." % max_ticks
        break

      if self.states[0].stats_en:
        self.tick_ctr += 1

      # select an active thread
      active_core = thread_select.xtick( self )

      # sanity checks
      if not self.states[active_core].active and not self.states[active_core].stop or active_core == -1:
        print "MT: Something wrong selected core is not active! tick: %d" % self.states[0].num_insts
        raise AssertionError

      # if all cores are not halting
      # NOTE: there always should be an active core selected
      if self.states[active_core]:
        s   = self.states[active_core]
        pc  = s.fetch_pc()
        mem = s.mem

        # fetch
        inst_bits = mem.iread( pc, 4 )

        try:
          # frontend
          inst, pre_exec_fun, exec_fun = self.decode( inst_bits )

          # collect linetrace pc here (pc before execute)
          pre_execute_pc = s.pc

          # only to collect LLFU and mem operations
          if pre_exec_fun:
            pre_exec_fun( s, inst )
          else:
            parallel_mode = s.wsrt_mode or s.spmd_mode
            if self.states[0].stats_en and parallel_mode:
              s.int_insts += 1

          #---------------------------------------------------------------
          # Collect stats
          #---------------------------------------------------------------
          # collect frontend stats here

          if s.spmd_mode:
            self.total_spmd     += 1
            self.total_parallel += 1
          elif s.wsrt_mode and s.task_mode:
            self.total_task     += 1
            self.total_wsrt     += 1
            self.total_parallel += 1
          elif s.wsrt_mode and s.runtime_mode:
            self.total_runtime  += 1
            self.total_wsrt     += 1
            self.total_parallel += 1

          # can't "draft"
          if s.pc != last_active_pc:
            # collect total instructions
            if s.spmd_mode:
              self.unique_spmd    += 1
              self.unique_insts   += 1
            elif s.wsrt_mode and s.task_mode:
              self.unique_task    += 1
              self.unique_insts   += 1
            elif s.wsrt_mode and s.runtime_mode:
              self.unique_runtime += 1
              self.unique_insts   += 1
            # update L0 state and stats here
            if (s.pc & l0_mask) in s.l0_buffer:
              s.insn_str = 'L:'
              if s.spmd_mode or s.wsrt_mode:
                s.l0_hits += 1
                self.total_imem_accesses += 1
                self.total_frontend += 1
            # add the line to the l0 buffer if there is a l0 buffer present
            if (s.pc & l0_mask) not in s.l0_buffer:
              s.insn_str = 'S:'
              if s.l0_buffer:
                s.l0_buffer.pop(0)
              s.l0_buffer.append( s.pc & l0_mask )
              if s.spmd_mode or s.wsrt_mode:
                self.unique_imem_accesses += 1
                self.total_imem_accesses += 1
                self.unique_frontend += 1
                self.total_frontend += 1

          # currently drafting
          else:
            s.insn_str = 'C:'
            if s.spmd_mode or s.wsrt_mode:
              self.total_coalesces += 1
              self.total_imem_accesses += 1
              self.total_frontend += 1

          # stats for data access
          if s.dmem:
            s.dmem = False
            s.dmemreq.addr = s.dmemreq.addr & dmem_mask
            # can coalesce load
            parallel_mode = s.wsrt_mode or s.spmd_mode
            if self.states[0].stats_en and parallel_mode:
              if s.dmemreq.type_ == 0 and last_mem_req.type_ == 0 and s.dmemreq.addr == last_mem_req.addr:
                self.total_dmem_accesses += 1
              else:
                self.unique_dmem_accesses += 1
                self.total_dmem_accesses += 1
          #---------------------------------------------------------------

          # backend
          exec_fun( s, inst )

          #---------------------------------------------------------------
          # Collect value similarity stats
          #---------------------------------------------------------------
          # can't draft
          if s.spmd_mode or s.wsrt_mode:
            if pre_execute_pc != last_active_pc:
              # stats for value similarity
              self.unique_executes += 1
              self.total_executes += 1
            # check drafting
            else:
              if s.operands.compare( last_operands ) and s.operands.valid:
                #print "Draft: %s" % ( inst.str )
                #print "   src0: v:%d v:%d %d %d" % ( s.operands.src0_val, last_operands.src0_val, s.operands.src0, last_operands.src0 )
                #print "   src1: v:%d v:%d %d %d" % ( s.operands.src1_val, last_operands.src1_val, s.operands.src1, last_operands.src1 )
                self.total_executes += 1
              else:
                self.unique_executes += 1
                self.total_executes += 1
          #---------------------------------------------------------------

          # save the current pc before retiring
          last_active_pc = pre_execute_pc

          # save operand state
          last_operands = s.operands

          # save current mem request
          if s.dmem:
            last_mem_req = s.dmemreq

        except FatalError as error:
          print "Exception in (pc: 0x%s), aborting!" % pad_hex( pc )
          print "Exception message: %s" % error.msg
          break

        if self.states[0].debug.enabled( "insts" ):
          print pad( "%x" % s.pc, 8, " ", False ),
          print "C%s a:%d i:%d s:%d c:%d g:%d l:%d %s %s %s" % (
                  active_core, s.active, s.istall, s.stall, s.clear, s.ganged, s.lockstep,
                  pad_hex( inst_bits ),
                  pad( inst.str, 12 ),
                  pad( "%d" % s.num_insts, 8 ), ),
          print

        if self.states[0].debug.enabled( "operands" ):
          print "C%s %s " % ( s.core_id,  pad( inst.str, 9 )),
          if s.operands.valid:
            if s.operands.src0_val:
              print pad_hex( s.operands.src0 ) + " ",
            if s.operands.src1_val:
              print pad_hex( s.operands.src1 ),
          print

        if self.states[0].debug.enabled( "regdump" ):
          print "C%d" % active_core
          s.rf.print_regs( per_row=4 )

        s.num_insts += 1
        if s.stats_en: s.stat_num_insts += 1

      # count steps in stats region
      if self.states[0].stats_en: self.total_steps += 1
      parallel_mode = self.states[0].wsrt_mode or self.states[0].spmd_mode
      if self.states[0].stats_en and not parallel_mode: self.serial_steps += 1

      # barrier stuff
      for state in self.states:
        if state.stop:
          state.barrier_ctr += 1

      # check for early exit at a barrier hint or if any core has hit the
      # max limit
      all_waiting = True
      reset_core  = False
      for state in self.states:
        if state.barrier_ctr == state.barrier_limit:
          reset_core = True
        if not state.barrier_ctr > 0:
          all_waiting = False

      # check which cores can proceed
      # NOTE: I currently opportunistically wakeup any other core that is
      # waiting when a core has hit the barrier limit
      if all_waiting or reset_core:
        waiting_cores = []
        for state in self.states:
          if state.barrier_ctr > 0:
            waiting_cores.append( state.core_id )

        for core in waiting_cores:
          curr_limit = self.states[core].barrier_limit
          if self.adaptive_hint:
            # found other cores
            if (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) > 1:
              self.states[core].barrier_limit = self.states[core].barrier_limit - self.barrier_delta if self.states[core].barrier_limit > self.barrier_delta else self.barrier_limit
              self.barrier_hits += 1
            # paid the cost at barrier and found no partner
            elif (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) == 1:
              self.states[core].barrier_limit = self.states[core].barrier_limit + self.barrier_delta if self.states[core].barrier_limit < self.barrier_limit else self.barrier_delta
              self.barrier_miss += 1
            # match because of sync up
            elif len( waiting_cores ) > 1:
              self.barrier_hits += 1
          else:
            # matched someone by waiting
            if (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) > 1:
              self.barrier_hits += 1
            # paid the cost at barrier and found no partner
            elif (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) == 1:
              self.barrier_miss += 1
            # match because of sync up
            elif len( waiting_cores ) > 1:
              self.barrier_hits += 1

          self.states[core].barrier_ctr = 0
          self.states[core].stop = False
          self.states[core].active = True
          self.states[core].pc += 4

      # linetrace
      if self.linetrace:
        if self.states[0].stats_en:
          print colors.cyan + "[C%d] " % active_core + colors.end,
          if self.states[active_core].active:
            s = self.states[active_core]
            parallel_mode = s.wsrt_mode or s.spmd_mode
            # core0 in serial section
            if self.color and not parallel_mode and active_core==0 :
              print colors.white + s.insn_str + pad( "%x |" % pre_execute_pc, 9, " ", False ) + colors.end
            # others in bthread control function
            elif self.color and not parallel_mode:
              print colors.blue + s.insn_str + pad( "%x |" % pre_execute_pc, 9, " ", False ) + colors.end
            # cores in spmd region
            elif self.color and s.spmd_mode:
              print colors.purple + s.insn_str + pad( "%x |" % pre_execute_pc, 9, " ", False ) + colors.end
            # cores executing tasks in wsrt region
            elif self.color and s.task_mode and parallel_mode:
              print colors.green + s.insn_str + pad( "%x |" % pre_execute_pc, 9, " ", False ) + colors.end
            # cores executing runtime function in wsrt region
            elif self.color and s.runtime_mode and parallel_mode:
              print colors.yellow + s.insn_str + pad( "%x |" % pre_execute_pc, 9, " ", False ) + colors.end
            # No color requested
            else:
              print s.insn_str + pad( "%x |" % pre_execute_pc, 9, " ", False ),
          else:
            print "#b" + pad( "%x |" % pre_execute_pc, 9, " ", False )

    # print stats
    print '\nDONE! Status =', self.states[0].status
    print 'Total ticks Simulated = %d\n' % self.tick_ctr

    print 'Serial steps in stats region = %d' % self.serial_steps
    print 'Total steps in stats region = %d' % self.total_steps
    parallel_region = self.total_steps - self.serial_steps
    if self.total_steps:
      print 'Percent insts in parallel region = %f\n' % ( 100*parallel_region/float( self.total_steps ) )

    # print instruction stats
    print 'Total insts in parallel regions = %d' % self.total_parallel
    print 'Unique insts in parallel regions = %d' % self.unique_insts
    redundant_insts = self.total_parallel - self.unique_insts
    if self.total_parallel:
      print 'Redundancy in parallel regions = %f' % ( 100*redundant_insts/float( self.total_parallel ) )
    print

    print "Total insts in spmd region = %d " % self.total_spmd
    print 'Unique spmd insts = %d' % self.unique_spmd
    redundant_spmd = self.total_spmd - self.unique_spmd
    if self.total_spmd:
      print 'Redundancy in spmd regions = %f' % ( 100*redundant_spmd/float( self.total_spmd ) )
    print

    print "Total insts in tasks = %d " % self.total_task
    print "Total insts in runtime = %d " % self.total_runtime
    print "Total insts in wsrt region = %d " % self.total_wsrt
    print 'Unique wsrt insts = %d' % ( self.unique_runtime + self.unique_task )
    redundant_wsrt = self.total_wsrt - ( self.unique_runtime + self.unique_task )
    if self.total_wsrt:
      print 'Redundancy in wsrt regions = %f' % ( 100*redundant_wsrt/float( self.total_wsrt ) )

    if self.total_wsrt:
      print "Percent of task insts = %f" % ( 100*self.total_task /float( self.total_wsrt ) )
    print 'Unique task insts = %d' % self.unique_task
    redundant_task = self.total_task - self.unique_task
    if self.total_task:
      print 'Redundancy in task regions = %f' % ( 100*redundant_task/float( self.total_task ) )

    print 'Unique runtime insts = %d' % self.unique_runtime
    redundant_runtime = self.total_runtime - self.unique_runtime
    if self.total_runtime:
      print 'Redundancy in runtime regions = %f' % ( 100*redundant_runtime/float( self.total_runtime ) )
    print

    # print imem accesses
    print 'Total instruction accesses in parallel regions = %d' % self.total_imem_accesses
    print 'Unique instruction accesses in parallel regions = %d' % self.unique_imem_accesses
    total_l0_hits = 0
    for state in self.states:
      total_l0_hits = total_l0_hits + state.l0_hits
      print 'L0 hits for core %d : %d' % ( state.core_id, state.l0_hits )
    print 'Total hits in Core L0 buffer: %d' % total_l0_hits
    print 'Total hits in SIMT L0 buffer: %d' % self.simt_l0_hits
    print 'Total number of coalesced instruction accesses: %d' % self.total_coalesces
    redundant_imem_accesses = self.total_imem_accesses - self.unique_imem_accesses
    if self.total_imem_accesses:
      print 'Savings for instruction accesses in parallel regions = %f' % ( 100*redundant_imem_accesses/float( self.total_imem_accesses ) )
      print 'Savings due to Core L0 buffers: %f' % ( 100*total_l0_hits/float( self.total_imem_accesses ) )
      print 'Savings due to SIMT L0 buffers: %f' % ( 100*self.simt_l0_hits/float( self.total_imem_accesses ) )
      print 'Savings due to coalescing: %f' % ( 100*self.total_coalesces/float( self.total_imem_accesses ) )
    print

    # print frontend stats
    print 'Total frontend accesses in parallel regions = %d' % self.total_frontend
    print 'Unique frontend accesses in parallel regions = %d' % self.unique_frontend
    redundant_frontend = self.total_frontend - self.unique_frontend
    if self.total_frontend:
      print 'Savings for frontend accesses in parallel regions = %f' % ( 100*redundant_frontend/float( self.total_frontend ) )
    print

    # print execute stats
    print 'Total number of executed instructions = %d' % self.total_executes
    print 'Unique executed instructions = %d' % self.unique_executes
    redundant_executes = self.total_executes - self.unique_executes
    if self.total_executes:
      print "Savings for executed instructions = %f" % ( 100*redundant_executes/float( self.total_executes ) )
    print

    # print data accesses
    print 'Total data accesses in parallel regions = %d' % self.total_dmem_accesses
    print 'Unique data accesses in parallel regions = %d' % self.unique_dmem_accesses
    redundant_dmem_accesses = self.total_dmem_accesses - self.unique_dmem_accesses
    if self.total_dmem_accesses:
      print 'Savings for data accesses in parallel regions = %f' % ( 100*redundant_dmem_accesses/float( self.total_dmem_accesses ) )
    print

    # total work
    total_work = self.total_imem_accesses + self.total_frontend + self.total_executes + self.total_dmem_accesses
    unique_work = self.unique_imem_accesses + self.unique_frontend + self.unique_executes + self.unique_dmem_accesses
    print 'Total work in parallel regions = %d' % total_work
    print 'Unique work in parallel regions = %d' % unique_work
    redundant_work = total_work - unique_work
    if total_work:
      print 'Savings in work in parallel regions = %f' % ( 100*redundant_work/float(total_work) )
    print

    # print instruction mix
    total_int_insts   = 0
    total_load_insts  = 0
    total_store_insts = 0
    total_amo_insts   = 0
    total_mdu_insts   = 0
    total_fpu_insts   = 0
    for state in self.states:
      total_int_insts   = total_int_insts   +  state.int_insts
      total_load_insts  = total_load_insts  +  state.load_insts
      total_store_insts = total_store_insts +  state.store_insts
      total_amo_insts   = total_amo_insts   +  state.amo_insts
      total_mdu_insts   = total_mdu_insts   +  state.mdu_insts
      total_fpu_insts   = total_fpu_insts   +  state.fpu_insts
    print 'Instructions mix in parallel regions'
    print 'integer = %d' % ( total_int_insts )
    print 'load    = %d' % ( total_load_insts )
    print 'store   = %d' % ( total_store_insts )
    print 'amo     = %d' % ( total_amo_insts )
    print 'mdu     = %d' % ( total_mdu_insts )
    print 'fpu     = %d' % ( total_fpu_insts )
    print

  #-----------------------------------------------------------------------
  # run
  #-----------------------------------------------------------------------
  def run( self ):
    self = hint( self, promote=True )

    #s = self.state

    max_insts = self.max_insts
    max_ticks = self.max_ticks
    jitdriver = self.jitdriver

    core_id = 0
    tick_ctr = self.tick_ctr

    # use proc 0 to determine if should be running
    while self.states[0].running:

      # check if we have reached the end of the maximum instructions and
      # exit if necessary
      if max_insts != 0 and self.states[0].num_insts >= max_insts:
        print "Reached the max_insts (%d), exiting." % max_insts
        break

      # check if we have reached the end of the maximum ticks and exit if
      # necessary
      if max_ticks != 0 and self.tick_ctr >= max_ticks:
        print "Reached the max_ticks (%d), exiting." % max_ticks
        break

      if self.states[0].stats_en:
        self.tick_ctr += 1

      #-------------------------------------------------------------------
      # IMPORTANT: 01/27/2018
      #
      # The simulation for a tick as shown below:
      #
      #     recovergence_manager.xtick()
      #
      #     for all cores:
      #       frontend
      #
      #     mem_coalescer.xtick()
      #     llfu_allocators.xtick()
      #
      #     for all cores:
      #       backend
      #
      #  - reconvergence manager: sets a thread to be active based on based
      #  on thread-selection policy under constrained instruction port
      #  bandwidth and hits in L0 buffers. In addition, a core that is
      #  waiting for another peer executing in lockstep mode (indicated by
      #  clear flag) is considered to be inactive as otherwise a core
      #  advances. If the core was not allocated any fetch bandwidth then
      #  it is deactivated unless it was stalling due to backend in which
      #  case it doesn't need any frontend functionality
      #
      #  - frontend loop: fetches an instruction for each active core that
      #  is not stalling decodes it and sets up requests to backend
      #  resources by calling the pre-execute function.
      #
      #  - mem_coalescer and llfu allocators: based on the requests as set
      #  up by the frontend and given resources, these objects figure out
      #  which cores can advance and which can't indicated by the stall
      #  flags.
      #
      # - backend loop: if a core is active and is not stalling the backend
      # is executed and any architectural state based on the instruction
      # type is updated. NOTE: If a core is waiting for a peer due to
      # lockstep execution it is deactivated and hence, the required
      # behavior of lockstep execution is realized.
      #
      # Given, the above behavior the redundancy stats must hence be
      # collected only if a core is active and is not stalling. The stats
      # are currently collected in the recovergence manager.
      #-------------------------------------------------------------------

      #-------------------------------------------------------------------
      # frontend resources
      #-------------------------------------------------------------------

      self.reconvergence_manager.xtick( self )

      # sanity checks
      active      = False
      all_waiting = True
      for i in xrange( self.ncores ):
        active |= self.states[i].active
        all_waiting = all_waiting and (self.states[i].stop or self.states[i].stall or self.states[i].clear)

      if not active and not all_waiting:
        print "Something wrong no cores are active! tick: %d" % self.states[0].num_insts
        raise AssertionError

      #-------------------------------------------------------------------
      # frontend
      #-------------------------------------------------------------------

      unique_pcs = []
      for core_id in xrange( self.ncores ):
        s = self.states[ core_id ]

        if s.active and not s.stall:
          pc = s.fetch_pc()
          mem = s.mem

          # fetch
          inst_bits = mem.iread( pc, 4 )

          # decode
          try:
            inst, pre_exec_fun, exec_fun = self.decode( inst_bits )

            if pre_exec_fun:
              pre_exec_fun( s, inst )
            else:
              parallel_mode = s.wsrt_mode or s.spmd_mode
              if self.states[0].stats_en and parallel_mode:
                s.int_insts += 1

            # record the function to be executed and the inst bits
            s.inst_bits = inst_bits
            s.inst      = inst
            s.exec_fun  = exec_fun

            #-------------------------------------------------------------
            # collect stats
            #-------------------------------------------------------------
            # NOTE: Look across all cores that will be fetched, find
            # instructions that are unique and count total.
            if s.pc not in unique_pcs:
              unique_pcs.append( s.pc )
              # collect total instructions
              if s.spmd_mode:
                self.unique_spmd    += 1
                self.unique_insts   += 1
              elif s.wsrt_mode and s.task_mode:
                self.unique_task    += 1
                self.unique_insts   += 1
              elif s.wsrt_mode and s.runtime_mode:
                self.unique_runtime += 1
                self.unique_insts   += 1

            # collect total instructions
            if s.spmd_mode:
              self.total_spmd     += 1
              self.total_parallel += 1
            elif s.wsrt_mode and s.task_mode:
              self.total_task     += 1
              self.total_wsrt     += 1
              self.total_parallel += 1
            elif s.wsrt_mode and s.runtime_mode:
              self.total_runtime  += 1
              self.total_wsrt     += 1
              self.total_parallel += 1

          except FatalError as error:
            print "Exception in decode (pc: 0x%s), aborting!" % pad_hex( pc )
            print "Exception message: %s" % error.msg
            break

      #frontend-----------------------------------------------------------

      if self.simt and len(unique_pcs) > self.inst_ports:
        print "SIMT mode can't have number of active PC's greater than available frontends! tick: %d" % ( self.states[0].num_insts )
        print
        for i in xrange( self.ncores ):
          s = self.states[ i ]
          print pad( "%x" % s.pc, 8, " ", False ),
          print "C%s a:%d i:%d s:%d c:%d g:%d l:%d %s %s %s" % (
                  i, s.active, s.istall, s.stall, s.clear, s.ganged, s.lockstep,
                  pad_hex( s.inst_bits ),
                  pad( s.inst.str, 12 ),
                  pad( "%d" % s.num_insts, 8 ), ),
          print
        raise AssertionError

      if self.states[0].debug.enabled( "insts" ):
        for i in xrange( self.ncores ):
          s = self.states[ i ]
          print pad( "%x" % s.pc, 8, " ", False ),
          print "C%s a:%d i:%d s:%d c:%d g:%d l:%d %s %s %s" % (
                  i, s.active, s.istall, s.stall, s.clear, s.ganged, s.lockstep,
                  pad_hex( s.inst_bits ),
                  pad( s.inst.str, 12 ),
                  pad( "%d" % s.num_insts, 8 ), ),
          print

      #-------------------------------------------------------------------
      # backend resources
      #-------------------------------------------------------------------

      self.dmem_coalescer.xtick( self )
      self.mdu_allocator.xtick ( self )
      self.fpu_allocator.xtick ( self )

      #-----------------------------------------------------------------------
      # dump trace
      #-----------------------------------------------------------------------
      # shreesha: dump trace shows actual execution trace

      if self.outfile and self.states[0].stats_en:
        self.out_fd.write( cvt_int2bytes( self.tick_ctr ) )
        pc_counts = {}
        for i in range( self.ncores ):
          if self.states[i].active and not self.states[i].stall:
            pc_counts[self.states[i].pc] = pc_counts.get(self.states[i].pc, 0) + 1

        for i in range( self.ncores ):
          task_mode    = False
          runtime_mode = False
          pc_count     = 0
          if self.states[i].active and not self.states[i].stall:
            if self.states[i].task_mode:    task_mode    = True
            if self.states[i].runtime_mode: runtime_mode = True
            pc_count = pc_counts[self.states[i].pc]
          self.out_fd.write( chr( task_mode ) )
          self.out_fd.write( chr( runtime_mode ) )
          self.out_fd.write( chr( pc_count ) )
          self.out_fd.write( chr( self.states[i].start_task ) )

      #-------------------------------------------------------------------
      # backend
      #-------------------------------------------------------------------

      # shreesha: linetrace
      # NOTE: collect the linetrace before commit as pc get's updated else
      pc_list = []
      unique_operands = {}
      for core in xrange( self.ncores ):

        s = self.states[ core ]

        s.start_task = False

        if self.linetrace:
          pc_list.append( s.pc )

        # NOTE: Be wary of bubble squeezing...
        if s.active and not s.stall:

          # execute and commit
          try:

            inst     = s.inst
            exec_fun = s.exec_fun

            exec_fun( s, inst )

            if s.spmd_mode or s.wsrt_mode:
              self.total_executes += 1
              match = False
              for key in unique_operands.keys():
                if s.operands.compare( key ) and s.operands.valid:
                  match = True
                  break
              if not match and s.operands.valid:
                unique_operands[ s.operands ] = s.operands

          except FatalError as error:
            print "Exception in execute (pc: 0x%s), aborting!" % pad_hex( s.pc )
            print "Exception message: %s" % error.msg
            break

        if self.states[0].debug.enabled( "operands" ):
          print "C%s %s " % ( s.core_id,  pad( s.inst.str, 9 )),
          if s.operands.valid:
            if s.operands.src0_val:
              print pad_hex( s.operands.src0 ) + " ",
            if s.operands.src1_val:
              print pad_hex( s.operands.src1 ),
          print

        if self.states[0].debug.enabled( "regdump" ):
          print "C%d" % core
          s.rf.print_regs( per_row=4 )

        if s.active and not s.stall:
          s.num_insts += 1
          if s.stats_en: s.stat_num_insts += 1

      #backend------------------------------------------------------------

      # value similarity stats
      self.unique_executes += len( unique_operands )

      # collect all stall stats
      for tc in self.states:
        if tc.istall:
          tc.imem_stalls += 1
        elif tc.stall:
          if   tc.dmem: tc.dmem_stalls += 1
          elif tc.mdu:  tc.mdu_stalls  += 1
          elif tc.fpu:  tc.fpu_stalls  += 1

      # count steps in stats region
      if self.states[0].stats_en: self.total_steps += 1

      parallel_mode = self.states[0].wsrt_mode or self.states[0].spmd_mode
      if self.states[0].stats_en and not parallel_mode: self.serial_steps += 1

      #if self.states[0].debug.enabled( "tpa" ):
      #  print "backend : [",
      #  for core in range( self.ncores ):
      #    if self.states[core].istall:
      #      print "%d:i," % core,
      #    elif self.states[core].stall:
      #      print "%d:s," % core,
      #    elif self.states[core].stop:
      #      print "%d:b," % core,
      #    elif self.states[core].clear:
      #      print "%d:w," % core,
      #    elif self.states[core].active:
      #      print "%d:a," % core,
      #    else:
      #      print "%d:n," %core,
      #  print "]"
      # update barrier counts for stalling cores

      for state in self.states:
        if state.stop:
          state.barrier_ctr += 1

      # check for early exit at a barrier hint or if any core has hit the
      # max limit
      all_waiting = True
      reset_core  = False
      for state in self.states:
        if state.barrier_ctr == state.barrier_limit:
          reset_core = True
        if not state.barrier_ctr > 0:
          all_waiting = False

      # check which cores can proceed
      # NOTE: I currently opportunistically wakeup any other core that is
      # waiting when a core has hit the barrier limit
      if all_waiting or reset_core:
        waiting_cores = []
        for state in self.states:
          if state.barrier_ctr > 0:
            waiting_cores.append( state.core_id )

        for core in waiting_cores:
          curr_limit = self.states[core].barrier_limit
          if self.adaptive_hint:
            # found other cores
            if (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) > 1:
              self.states[core].barrier_limit = self.states[core].barrier_limit - self.barrier_delta if self.states[core].barrier_limit > self.barrier_delta else self.barrier_limit
              self.barrier_hits += 1
            # paid the cost at barrier and found no partner
            elif (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) == 1:
              self.states[core].barrier_limit = self.states[core].barrier_limit + self.barrier_delta if self.states[core].barrier_limit < self.barrier_limit else self.barrier_delta
              self.barrier_miss += 1
            # match because of sync up
            elif len( waiting_cores ) > 1:
              self.barrier_hits += 1
          else:
            # matched someone by waiting
            if (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) > 1:
              self.barrier_hits += 1
            # paid the cost at barrier and found no partner
            elif (self.states[core].barrier_ctr == self.states[core].barrier_limit) and len( waiting_cores ) == 1:
              self.barrier_miss += 1
            # match because of sync up
            elif len( waiting_cores ) > 1:
              self.barrier_hits += 1

          self.states[core].barrier_ctr = 0
          self.states[core].stop = False
          self.states[core].active = True
          self.states[core].pc += 4

      # shreesha: linetrace
      if self.linetrace:
        if self.states[0].stats_en:
          for i in range( self.ncores ):
            stall  = False
            clear  = False
            active = False
            #NOTE: the linetrace is not perfect but is a start
            #lockstep execution is a pain to show
            stall  = self.states[i].stall or self.states[i].istall
            clear  = self.states[i].clear
            active = self.states[i].active

            if active and not ( stall or clear):
              parallel_mode = self.states[i].wsrt_mode or self.states[i].spmd_mode
              # core0 in serial section
              if self.color and not parallel_mode and i ==0 :
                print colors.white + self.states[i].insn_str + pad( "%x |" % pc_list[i], 9, " ", False ) + colors.end,
              # others in bthread control function
              elif self.color and not parallel_mode:
                print colors.blue + self.states[i].insn_str + pad( "%x |" % pc_list[i], 9, " ", False ) + colors.end,
              # cores in spmd region
              elif self.color and self.states[i].spmd_mode:
                print colors.purple + self.states[i].insn_str + pad( "%x |" % pc_list[i], 9, " ", False ) + colors.end,
              # cores executing tasks in wsrt region
              elif self.color and self.states[i].task_mode and parallel_mode:
                print colors.green + self.states[i].insn_str + pad( "%x |" % pc_list[i], 9, " ", False ) + colors.end,
              # cores executing runtime function in wsrt region
              elif self.color and self.states[i].runtime_mode and parallel_mode:
                print colors.yellow + self.states[i].insn_str + pad( "%x |" % pc_list[i], 9, " ", False ) + colors.end,
              # No color requested
              else:
                print  self.states[i].insn_str + pad( "%x |" % pc_list[i], 9, " ", False ),
            elif stall:
              if self.states[i].istall:
                print pad( "#i |", 11, " ", False ),
              if self.states[i].dmem:
                print pad( "#d |", 11, " ", False ),
              elif self.states[i].mdu:
                print pad( "#m |", 11, " ", False ),
              elif self.states[i].fpu:
                print pad( "#f |", 11, " ", False ),
            elif clear:
                print pad( "#w |", 11, " ", False ),
            else:
              print pad( " |", 11, " ", False ),
          print

    if self.outfile:
      self.out_fd.close()

    # print stats
    print '\nDONE! Status =', self.states[0].status
    print 'Total ticks Simulated = %d\n' % self.tick_ctr

    print 'Serial steps in stats region = %d' % self.serial_steps
    print 'Total steps in stats region = %d' % self.total_steps
    parallel_region = self.total_steps - self.serial_steps
    if self.total_steps:
      print 'Percent insts in parallel region = %f\n' % ( 100*parallel_region/float( self.total_steps ) )

    # print instruction stats
    print 'Total insts in parallel regions = %d' % self.total_parallel
    print 'Unique insts in parallel regions = %d' % self.unique_insts
    redundant_insts = self.total_parallel - self.unique_insts
    if self.total_parallel:
      print 'Redundancy in parallel regions = %f' % ( 100*redundant_insts/float( self.total_parallel ) )
    print

    print "Total insts in spmd region = %d " % self.total_spmd
    print 'Unique spmd insts = %d' % self.unique_spmd
    redundant_spmd = self.total_spmd - self.unique_spmd
    if self.total_spmd:
      print 'Redundancy in spmd regions = %f' % ( 100*redundant_spmd/float( self.total_spmd ) )
    print

    print "Total insts in tasks = %d " % self.total_task
    print "Total insts in runtime = %d " % self.total_runtime
    print "Total insts in wsrt region = %d " % self.total_wsrt
    print 'Unique wsrt insts = %d' % ( self.unique_runtime + self.unique_task )
    redundant_wsrt = self.total_wsrt - ( self.unique_runtime + self.unique_task )
    if self.total_wsrt:
      print 'Redundancy in wsrt regions = %f' % ( 100*redundant_wsrt/float( self.total_wsrt ) )

    if self.total_wsrt:
      print "Percent of task insts = %f" % ( 100*self.total_task /float( self.total_wsrt ) )
    print 'Unique task insts = %d' % self.unique_task
    redundant_task = self.total_task - self.unique_task
    if self.total_task:
      print 'Redundancy in task regions = %f' % ( 100*redundant_task/float( self.total_task ) )

    print 'Unique runtime insts = %d' % self.unique_runtime
    redundant_runtime = self.total_runtime - self.unique_runtime
    if self.total_runtime:
      print 'Redundancy in runtime regions = %f' % ( 100*redundant_runtime/float( self.total_runtime ) )
    print

    # print imem accesses
    print 'Total instruction accesses in parallel regions = %d' % self.total_imem_accesses
    print 'Unique instruction accesses in parallel regions = %d' % self.unique_imem_accesses
    total_l0_hits = 0
    for state in self.states:
      total_l0_hits = total_l0_hits + state.l0_hits
      print 'L0 hits for core %d : %d' % ( state.core_id, state.l0_hits )
    print 'Total hits in Core L0 buffer: %d' % total_l0_hits
    print 'Total hits in SIMT L0 buffer: %d' % self.simt_l0_hits
    print 'Total number of coalesced instruction accesses: %d' % self.total_coalesces
    redundant_imem_accesses = self.total_imem_accesses - self.unique_imem_accesses
    if self.total_imem_accesses:
      print 'Savings for instruction accesses in parallel regions = %f' % ( 100*redundant_imem_accesses/float( self.total_imem_accesses ) )
      print 'Savings due to Core L0 buffers: %f' % ( 100*total_l0_hits/float( self.total_imem_accesses ) )
      print 'Savings due to SIMT L0 buffers: %f' % ( 100*self.simt_l0_hits/float( self.total_imem_accesses ) )
      print 'Savings due to coalescing: %f' % ( 100*self.total_coalesces/float( self.total_imem_accesses ) )
    print

    # print frontend stats
    print 'Total frontend accesses in parallel regions = %d' % self.total_frontend
    print 'Unique frontend accesses in parallel regions = %d' % self.unique_frontend
    redundant_frontend = self.total_frontend - self.unique_frontend
    if self.total_frontend:
      print 'Savings for frontend accesses in parallel regions = %f' % ( 100*redundant_frontend/float( self.total_frontend ) )
    print

    # print execute stats
    print 'Total number of executed instructions = %d' % self.total_executes
    print 'Unique executed instructions = %d' % self.unique_executes
    redundant_executes = self.total_executes - self.unique_executes
    if self.total_executes:
      print "Savings for executed instructions = %f" % ( 100*redundant_executes/float( self.total_executes ) )
    print

    # print data accesses
    print 'Total data accesses in parallel regions = %d' % self.total_dmem_accesses
    print 'Unique data accesses in parallel regions = %d' % self.unique_dmem_accesses
    redundant_dmem_accesses = self.total_dmem_accesses - self.unique_dmem_accesses
    if self.total_dmem_accesses:
      print 'Savings for data accesses in parallel regions = %f' % ( 100*redundant_dmem_accesses/float( self.total_dmem_accesses ) )
    print

    # total work
    total_work = self.total_imem_accesses + self.total_frontend + self.total_executes + self.total_dmem_accesses
    unique_work = self.unique_imem_accesses + self.unique_frontend + self.unique_executes + self.unique_dmem_accesses
    print 'Total work in parallel regions = %d' % total_work
    print 'Unique work in parallel regions = %d' % unique_work
    redundant_work = total_work - unique_work
    if total_work:
      print 'Savings in work in parallel regions = %f' % ( 100*redundant_work/float(total_work) )
    print

    # barrier stats
    print "Barrier hits: ", self.barrier_hits
    print "Barrier misses: ", self.barrier_miss
    print "Total tasks: ", self.num_tasks

    # print instruction mix
    total_int_insts   = 0
    total_load_insts  = 0
    total_store_insts = 0
    total_amo_insts   = 0
    total_mdu_insts   = 0
    total_fpu_insts   = 0
    for state in self.states:
      total_int_insts   = total_int_insts   +  state.int_insts
      total_load_insts  = total_load_insts  +  state.load_insts
      total_store_insts = total_store_insts +  state.store_insts
      total_amo_insts   = total_amo_insts   +  state.amo_insts
      total_mdu_insts   = total_mdu_insts   +  state.mdu_insts
      total_fpu_insts   = total_fpu_insts   +  state.fpu_insts
    print 'Instructions mix in parallel regions'
    print 'integer = %d' % ( total_int_insts )
    print 'load    = %d' % ( total_load_insts )
    print 'store   = %d' % ( total_store_insts )
    print 'amo     = %d' % ( total_amo_insts )
    print 'mdu     = %d' % ( total_mdu_insts )
    print 'fpu     = %d' % ( total_fpu_insts )
    print

    # print stall counts
    total_imem_stalls = 0
    total_dmem_stalls = 0
    total_mdu_stalls  = 0
    total_fpu_stalls  = 0
    print pad( "Core |", 12, " ", False ),
    print pad( "imem# |", 12, " ", False ),
    print pad( "dmem# |", 12, " ", False ),
    print pad( "mdu# |", 12, " ", False ),
    print pad( "fpu# |", 12, " ", False )
    for state in self.states:
      print pad( "%d |" % state.core_id, 12, " ", False ),
      total_imem_stalls += state.imem_stalls
      print pad( "%d |" % state.imem_stalls, 12, " ", False ),
      total_dmem_stalls += state.dmem_stalls
      print pad( "%d |" % state.dmem_stalls, 12, " ", False ),
      total_mdu_stalls  += state.mdu_stalls
      print pad( "%d |" % state.mdu_stalls, 12, " ", False ),
      total_fpu_stalls  += state.fpu_stalls
      print pad( "%d |" % state.fpu_stalls, 12, " ", False )

    print pad( "Total |", 12, " ", False ),
    print pad( "%d |" % total_imem_stalls, 12, " ", False ),
    print pad( "%d |" % total_dmem_stalls, 12, " ", False ),
    print pad( "%d |" % total_mdu_stalls, 12, " ", False ),
    print pad( "%d |" % total_fpu_stalls, 12, " ", False )
    print

    # show all stats
    for i, state in enumerate( self.states ):
      print 'Core %d Instructions Executed = %d' % ( i, state.num_insts )

  #-----------------------------------------------------------------------
  # get_entry_point
  #-----------------------------------------------------------------------
  # generates and returns the entry_point function used to start the
  # simulator

  def get_entry_point( self ):
    def entry_point( argv ):

      # set the trace_limit parameter of the jitdriver
      if self.jit_enabled:
        set_param( self.jitdriver, "trace_limit", self.default_trace_limit )

      filename_idx       = 0
      debug_flags        = []
      debug_starts_after = 0
      testbin            = False
      max_insts          = 0
      envp               = []
      core_type          = 0
      stats_core_type    = 0
      accel_rf           = False
      # shreesha: runtime metadata
      runtime_md         = None

      # we're using a mini state machine to parse the args

      prev_token = ""

      # list of tokens that require an additional arg

      tokens_with_args = [ "-h", "--help",
                           "-e", "--env",
                           "-d", "--debug",
                           "--max-insts",
                           "--max-ticks",
                           "--jit",
                           "--ncores",
                           "--core-switch-ival",
                           "--pkernel",
                           "--core-type",
                           "--stats-core-type",
                           "--linetrace",
                           "--lockstep",
                           "--color",
                           "--analysis",
                           "--runtime-md",
                           "--outfile",
                           "--inst-ports",
                           "--data-ports",
                           "--mdu-ports",
                           "--fpu-ports",
                           "--icache-line-sz",
                           "--dcache-line-sz",
                           "--l0-buffer-sz",
                           "--adaptive-hint",
                           "--barrier-limit",
                           "--barrier-delta",
                           "--icoalesce",
                           "--iword-match",
                           "--simt",
                           "--sched-limit",
                           "--limit-lockstep",
                           "--mt",
                         ]

      # go through the args one by one and parse accordingly

      for i in xrange( 1, len( argv ) ):
        token = argv[i]

        if prev_token == "":

          if token == "--help" or token == "-h":
            print self.help_message % ( self.arch_name, argv[0] )
            return 0

          elif token == "--test":
            testbin = True

          elif token == "--accel-rf":
            accel_rf = True

          elif token == "--debug" or token == "-d":
            prev_token = token
            # warn the user if debugs are not enabled for this translation
            if not Debug.global_enabled:
              print "WARNING: debugs are not enabled for this translation. " + \
                    "To allow debugs, translate with --debug option."

          elif token == "--linetrace":
            self.linetrace = True

          elif token == "--color":
            self.color = True

          elif token == "--icoalesce":
            self.icoalesce = False

          elif token == "--iword-match":
            self.iword_match = False

          elif token == "--simt":
            self.simt = True

          elif token == "--limit-lockstep":
            self.limit_lockstep = True

          elif token == "--adaptive-hint":
            self.adaptive_hint = True

          elif token == "--mt":
            self.mt = True

          elif token in tokens_with_args:
            prev_token = token

          elif token[:1] == "-":
            # unknown option
            print "Unknown argument %s" % token
            return 1

          else:
            # this marks the start of the program name
            filename_idx = i
            break

        else:
          if prev_token == "--env" or prev_token == "-e":
            envp.append( token )

          elif prev_token == "--debug" or prev_token == "-d":
            # if debug start after provided (using a colon), parse it
            debug_tokens = token.split( ":" )
            if len( debug_tokens ) > 1:
              debug_starts_after = int( debug_tokens[1] )

            debug_flags = debug_tokens[0].split( "," )

          elif prev_token == "--max-insts":
            self.max_insts = int( token )

          elif prev_token == "--max-ticks":
            self.max_ticks = int( token )

          elif prev_token == "--jit":
            # pass the jit flags to rpython.rlib.jit
            set_user_param( self.jitdriver, token )

          elif prev_token == "--ncores":
            self.ncores = int( token )
            self.active_cores = self.ncores

          elif prev_token == "--core-switch-ival":
            self.core_switch_ival = int( token )

          elif prev_token == "--pkernel":
            self.pkernel_bin = token

          elif prev_token == "--core-type":
            core_type = int( token )

          elif prev_token == "--stats-core-type":
            stats_core_type = int( token )

          elif prev_token == "--analysis":
            self.reconvergence = int( token )

          elif prev_token == "--lockstep":
            self.lockstep = int( token )

          elif prev_token == "--runtime-md":
            runtime_md = token

          elif prev_token == "--outfile":
            self.outfile = token

          elif prev_token == "--inst-ports":
            self.inst_ports = int(token)

          elif prev_token == "--data-ports":
            self.data_ports = int(token)

          elif prev_token == "--mdu-ports":
            self.mdu_ports = int(token)

          elif prev_token == "--fpu-ports":
            self.fpu_ports = int(token)

          elif prev_token == "--icache-line-sz":
            self.icache_line_sz = int(token)
            if not self.icache_line_sz % 4 == 0:
              print "Insn cache line size must be word aligned!"
              return 1

          elif prev_token == "--dcache-line-sz":
            self.dcache_line_sz = int(token)
            if not self.dcache_line_sz % 4 == 0:
              print "Data cache line size must be word aligned!"
              return 1

          elif prev_token == "--l0-buffer-sz":
            self.l0_buffer_sz = int(token)

          elif prev_token == "--barrier-limit":
            self.barrier_limit = int(token)

          elif prev_token == "--barrier-delta":
            self.barrier_delta = int(token)

          elif prev_token == "--sched-limit":
            self.sched_limit = int(token)

          prev_token = ""

      if filename_idx == 0:
        print "You must supply a filename"
        return 1

      # create a Debug object which contains the debug flags

      self.debug = Debug( debug_flags, debug_starts_after )

      filename = argv[ filename_idx ]

      # args after program are args to the simulated program

      run_argv = argv[ filename_idx : ]

      # Open the executable for reading

      try:
        exe_file = open( filename, 'rb' )

      except IOError:
        print "Could not open file %s" % filename
        return 1

      # Call ISA-dependent init_state to load program, initialize memory
      # etc.

      self.init_state( exe_file, filename, run_argv, envp, testbin )

      # set the core type and stats core type

      for i in range( self.ncores ):
        self.states[i].core_type = core_type
        self.states[i].stats_core_type = stats_core_type
        self.states[i].sim_ptr = self
        if self.l0_buffer_sz > 0:
          self.states[i].l0_buffer = [0]*self.l0_buffer_sz
        # set lockstep execution state
        if self.lockstep == 1:
          self.states[i].lockstep = True
        elif self.lockstep == 2:
          self.task_lockstep = True
        # barrier limit
        if self.adaptive_hint:
          self.states[i].barrier_limit = self.barrier_delta
        else:
          self.states[i].barrier_limit = self.barrier_limit

      # set accel rf mode

      for i in range( self.ncores ):
        self.states[i].accel_rf = accel_rf

      # pass the state to debug for cycle-triggered debugging

      # TODO: not sure about this, just pass states[0]
      self.debug.set_state( self.states[0] )

      # Close after loading

      exe_file.close()

      # shreesha: runtime metadata
      if runtime_md:
        try:
          runtime_md_file = open( runtime_md, 'rb' )
          addr_list    = [ int(n) for n in runtime_md_file.readline().strip().split(",") ]
          name_list    = runtime_md_file.readline().strip().split(",")
          for i in range( self.ncores ):
            for x,addr in enumerate(addr_list):
              self.states[i].runtime_dict[addr] = name_list[x]
          runtime_md_file.close()
        except IOError:
          print "Could not open the runtime-md file %s " % runtime_md
          return 1

      if self.outfile:
        try:
          self.out_fd = open( self.outfile, "w" )
        except:
          print "Could not open dump file: %", self.outfile
          return 1

      #-----------------------------------------------------------------
      # TPA microarchitectural parameters and configuration
      #-----------------------------------------------------------------

      print "Executing in MT mode: ", bool( self.mt )

      # print the reconvergence scheme used
      if   self.reconvergence == 0: print "No reconvergence"
      elif self.reconvergence == 1: print "Min-pc, round-robin"
      elif self.reconvergence == 2: print "Min-sp/pc, round-robin"
      else:
        print "Invalid option for recovergence. Try --help for options."
        return 1
      # shreesha: default number of instruction ports
      if self.inst_ports == 0 and not self.mt:
        self.inst_ports = self.ncores
      elif self.inst_ports == 0 and self.mt:
        self.inst_ports = 1
      print "Inst ports: ", self.inst_ports

      # shreesha: default icache-line-sz
      if self.icache_line_sz == 0:
        self.icache_line_sz = self.ncores * 4
      print "Insn cache line size: %d" % self.icache_line_sz

      # shreesha: l0 buffer size
      print "SIMT Frontend: ", bool(self.simt)
      if self.simt:
        print "  setting the word match to be true!"
        self.iword_match = True
      print "SIMT L0 buffer : ", bool(self.simt) and self.l0_buffer_sz > 0
      print "L0 buffer size in cache lines: %d" % ( self.l0_buffer_sz )

      # shreesha: configure reconvergence manager
      self.reconvergence_manager.configure( self.ncores, self.icoalesce, self.iword_match, self.icache_line_sz, self.sched_limit )

      # shreesha: default dcache-line-sz
      if self.dcache_line_sz == 0:
        self.dcache_line_sz = self.ncores * 4
      mask_bits = ~( self.dcache_line_sz - 1 )
      mask = mask_bits & 0xFFFFFFFF
      print "Data cache line size: %d, mask: %x" % ( self.dcache_line_sz, mask )

      # lockstep option
      print "Limiting lockstep group size: ", bool( self.limit_lockstep )

      # shreesha: default number of data ports
      if self.data_ports == 0:
        self.data_ports = self.ncores
      print "Data ports: ", self.data_ports, " with: ",
      if self.lockstep == 0:
        print "No lockstep sharing"
      elif self.lockstep == 1:
        print "Lockstep sharing"
      elif self.lockstep == 2:
        print "Task-aware adaptive lockstep sharing"

      # shreesha: configure dmem coalescer
      self.dmem_coalescer.configure( self.ncores, self.data_ports, self.dcache_line_sz, self.lockstep, self.limit_lockstep )

      # shreesha: default number of mdu ports
      if self.mdu_ports == 0:
        self.mdu_ports = self.ncores
      print "MDU  ports: ", self.mdu_ports, " with: ",
      if self.lockstep == 0:
        print "No lockstep sharing"
      elif self.lockstep == 1:
        print "Lockstep sharing"
      elif self.lockstep == 2:
        print "Task-aware adaptive lockstep sharing"

      # shreesha: configure mdu allocator
      self.mdu_allocator.configure( self.ncores, self.mdu_ports, self.lockstep, self.limit_lockstep )

      # shreesha: default number of fpu ports
      if self.fpu_ports == 0:
        self.fpu_ports = self.ncores
      print "FPU  ports: ", self.fpu_ports, " with: ",
      if self.lockstep == 0:
        print "No lockstep sharing"
      elif self.lockstep == 1:
        print "Lockstep sharing"
      elif self.lockstep == 2:
        print "Task-aware adaptive lockstep sharing"

      # shreesha: configure fpu allocator
      self.fpu_allocator.configure( self.ncores, self.fpu_ports, self.lockstep, self.limit_lockstep )

      print "Barrier limit: ", self.barrier_limit
      print "Adaptive barriers enabled: ", bool( self.adaptive_hint )
      if self.barrier_delta == 0:
        self.barrier_delta = 50
      print "Barrier Delta: ", self.barrier_delta

      if self.sched_limit == 0:
        self.sched_limit = self.ncores
      print "Scheduling limit: ", self.sched_limit

      #-----------------------------------------------------------------

      # Execute the program

      if self.mt:
        self.run_mt()
      else:
        self.run()

      return 0

    return entry_point

  #-----------------------------------------------------------------------
  # target
  #-----------------------------------------------------------------------
  # Enables RPython translation of our interpreter.

  def target( self, driver, args ):

    # if --debug flag is provided in translation, we enable debug printing

    if "--debug" in args:
      print "Enabling debugging"
      Debug.global_enabled = True
    else:
      print "Disabling debugging"

    # form a name
    exe_name = "pydgin-%s" % self.arch_name.lower()
    if driver.config.translation.jit:
      exe_name += "-jit"
    else:
      exe_name += "-nojit"

    if Debug.global_enabled:
      exe_name += "-debug"

    print "Translated binary name:", exe_name
    driver.exe_name = exe_name

    # NOTE: RPython has an assertion to check the type of entry_point to
    # generates a function type
    #return self.entry_point, None
    return self.get_entry_point(), None

#-------------------------------------------------------------------------
# init_sim
#-------------------------------------------------------------------------
# Simulator implementations need to call this function at the top level.
# This takes care of adding target function to top level environment and
# running the simulation in interpreted mode if directly called
# ( __name__ == "__main__" )

def init_sim( sim ):

  # this is a bit hacky: we get the global variables of the caller from
  # the stack frame to determine if this is being run top level and add
  # target function required by rpython toolchain

  caller_globals = sys._getframe(1).f_globals
  caller_name    = caller_globals[ "__name__" ]

  # add target function to top level

  caller_globals[ "target" ] = sim.target

  #-----------------------------------------------------------------------
  # main
  #-----------------------------------------------------------------------
  # Enables CPython simulation of our interpreter.
  if caller_name == "__main__":
    # enable debug flags in interpreted mode
    Debug.global_enabled = True
    sim.get_entry_point()( sys.argv )

