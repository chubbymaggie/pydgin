================================================================================
Related Work
================================================================================

--------------------------------------------------------------------------------
ISS JIT Auto-Generation from ADL
--------------------------------------------------------------------------------

Citation::

  @article{wagstaff-archc-jit-dac2013,
    author    = {Harry Wagstaff and Miles Gould and
                 Bj\"{o}rn Franke and Nigel Topham},
    title     = {Early partial evaluation in a JIT-compiled, retargetable
                 instruction set simulator generated from a high-level
                 architecture description},
    journal   = DAC,
    month     = JUN,
    year      = {2013},
  }

ABSTRACT:

Modern processor design tools integrate in their workflows generators for
instruction set simulators (Iss) from architecture descriptions. Whilst these
generated simulators are useful for design evaluation and software development,
they suffer from poor performance. We present an ultra-fast Jit-compiled Iss
generated from an ArchC description. We also introduce a novel partial
evaluation optimisation, which further improves Jit compilation time and code
quality. This results in a simulation rate of 510Mips for an Arm target across
45 Eembc and Spec benchmarks. On average, our Iss is 1.7 times faster than
Simit-Arm, one of the fastest Iss generated from an architecture description.

Notes:

- modern processor design suites integrate ADL->ISS generators,
  but slower than hand-coded

- fastest ISS: utilize DBT with parallel JIT compiler + possibly interleave
  detailed performance model for cycle-accurate pipeline modeling
  (hand-coded for performance reasons, not easily retargetable)

- Naive ADL->JIT+DBT+ISS performance issues:
  1. poor quality of JIT generated code
  2. long compilation times

  CAUSE: complex behavior of instructions, exec path depends on uarch state

- evaluation: ARMv5 against 45 EEMBC1.1 and SPECINT2006 Benchmarks

  - 191 MIPS: naive JIT generator
  - 510 MIPS: early partial evaluation optimization
  -  24 MIPS: original ArchC Simulator
  -   6 MIPS: FaC-SIM
  - 300 MIPS: SIMIT-ARM (manual instruction specialization)
  - 635 MIPS: QEMU-ARM (sacrifices instruction observability for perf)

- related work:

  **Designing a CPU model: from a pseudo-formal document to fast code.**

  An interesting approach is presented in [3]. It aims at generating an Iss
  from a pseudo-formal document such as a datasheet. However, this approach
  still requires lots of manual adaptation.

--------------------------------------------------------------------------------

Citation::

  @string{DDECS    = {Design and Diagnostics of Electronic Circuits & Systems
                      (DDECS)}}

  @article{prikryl-isac-jit-ddecs2011,
    author    = {Zden\v{e}k P\v{r}ikryl and Jakub K\v{r}oustek and
                 Tom\'{a}\v{s} Hru\v{s}ka and Du\v{s}an Kol\'{a}\v{r}},
    title     = {Fast Just-In-Time Translated Simulator for ASIP Design},
    journal   = DDECS,
    month     = APR,
    year      = {2011},
  }

ABSTRACT:

The fast and accurate processor simulator is an essential tool for effective
design of modern high-performance application-specific instruction set
processors. The nowadays trend of ASIP design is focused on automatic simulator
generation based on a processor description in an architecture description
language. The simulator is used for testing and validation of designed
processor or target application. Furthermore, the simulator can produce the
profiling information. This information can aid design space exploration and
the processor and target application optimization. In this paper, we present
the concept of automatically generated just-in-time translated simulator with
the profiling capabilities. This simulator is very fast, and it is generated in
a short time. It can be even used for simulation of special applications, such
as applications with self-modifying code or applications for systems with
external memories. The experimental results can be found at the end of the
paper.

--------------------------------------------------------------------------------

Citation::

  @string{RAPIDO   = {Workshop on Rapid Simulation and Performance Evalution:
                      Methods and Tools (RAPIDO)}

  @article{brandner-jit-isa-rapido2009,
    title     = {Fast and Accurate Simulation using the
                 LLVM Compiler Framework},
    author    = {Florian Brandner and Andreas Fellnhofer and
                 Andreas Krall and David Riegler},
    journal   = RAPIDO,
    month     = ???,
    year      = {2009},
  }

ABSTRACT:

Development of future generation computer architectures requires fast and
accurate simulation tools that allow to test, verify, and analyze the behavior
of the given architecture along with the intended workload. We present a
simulation framework based on a structural architecture description language
that uses the open source compiler infrastructure LLVM to dynamically translate
instruction sequences of the simulated architecture into machine instructions
of the host machine. We show that the optimizations in the simulator and the
LLVM compiler lead to an outstanding runtime performance: A 5-stage MIPS core
is simulated at a peak performance of up to 800 MHz.

NOTE:

- We present a retargetable dynamic-compiling simulation framework based on the
  open source compiler infrastructure LLVM [LA04]. The LLVM just-in-time
  compiler generates high-quality code, such that the achieved simulation speed
  reaches up to several hundred MHz. Retargeting the simulator requires only
  minimal programming effort, because all architectural features are derived
  from an architecture model specified using a structural architecture
  description language (ADL). Our ADL also allows to derive other software
  tools, such as a C compiler [BEK07], from the same architecture model.

- All architecture dependent simulation functions are derived from structural
  architecture specifications that can also be used to generate a VHDL
  processor model and a C compiler. The LLVM just-in-time compiler is used to
  compile basic blocks and non-linear regions of the simulated program to
  native code of the host machine. Optimizations of the simulator generator and
  the compiler framework enable a peak performance of the simulation speed of
  up to 800 MHz for the MIPS architecture. Future work on reducing the compile
  time is necessary to reduce the gap between the average simulation speed of
  47 MHz for the MIPS (79 MHz for the VLIW CHILI) and the peak performance.

--------------------------------------------------------------------------------

Citation::

  @article{nohl-lisa-jit-dac2002,
    author    = {Achim Nohl and Gunnar Braun and Oliver Schliebusch and Rainer
                 Leupers and Heinrich Meyr and Andreas Hoffmann},
    title     = {A Universal Technique for Fast and Flexible Instruction-Set
                 Architecture Simulation},
    journal   = DAC,
    month     = JUN,
    year      = {2002},
  }

ABSTRACT:

In the last decade, instruction-set simulators have become an essential
development tool for the design of new programmable architectures.
Consequently, the simulator performance is a key factor for the overall
design efficiency. Based on the extremely poor performance of commonly used
interpretive simulators, research work on fast compiled instruction-set
simulation was started ten years ago. However, due to the restrictiveness of
the compiled technique, it has not been able to push through in commercial
products. This paper presents a new retargetable simulation technique which
combines the performance of traditional compiled simulators with the
flexibility of interpretive simulation. This technique is not limited to any
class of architectures or applications and can be utilized from a.rchi-
tecture exploration up to end-user software development. The work-flow and the
applicability of the so-called just-intime cache compiled simulation
(JIT-CCS) technique will be demonstrated by means of state of the art real
world architectures.

NOTES:

- The presented technique is integrated in the retargetable LISA processor
  design platform [2]. A generator back-end for the LISA 2.0 processor compiler
  has been developed, which automatically comtructs a JIT-CCS simulator from a
  LISA machine description.
- The Just-In-Time Cache Compiled Simulation (JIT-CCS) technique presented in
  this paper has been developed with the intention to combine the full
  flexibility of interpretive simulators with the speed of the compiled
  principle. The basic idea is to integrate the simulation compiler into the
  simulator. The compilation of an instruction takes place at simulator
  run-time, just-in-time before the instruction is going to be executed.
  Subsequently, the extracted inforniation is stored in a simulation cache
  for the direct reuse in a repeated execution of the program address. The
  simulator recognizes if the program code of a previously executed address
  has changed and initiates a re-compilation.
- The behavioral C code of all LISA operations is pre-compiled into C-functions
  which are part of the simulator. The JIT simulation compiler selects the
  appropriate operations, which are required to simulate an instruction, on the
  basis of the coding information. References to the selected C-functions are
  subsequently stored in the simulation cache. These references are utilized by
  the simulator to execute the instructions' behavior.

--------------------------------------------------------------------------------

Citation::

  @string{TCAD     = {IEEE Trans. on Computer-Aided Design of Integrated Circuits
                      and Systems (TCAD)}}

  @article{braun-lisa-jit-tcad2004,
    author    = {Gunnar Braun and Achim Nohl and Andreas Hoffmann and
                 Oliver Schliebusch and Rainer Leupers and Heinrich Meyr},
    title     = {A Universal Technique for Fast and Flexible Instruction-Set
                 Architecture Simulation},
    journal   = TCAD,
    month     = JUN,
    year      = {2004},
  }

ABSTRACT:

Today, designers of next-generation embedded processors and software are
increasingly faced with short product lifetimes. The resulting time-to-market
constraints are contradicting the continually growing processor complexity.
Nevertheless, an extensive design-space exploration and product verification
is indispensable for a successful market launch. In the last decade, in-
struction-set simulators have become an essential development tool for the
design of new programmable architectures. Consequently, the simulator
performance is a key factor for the overall design efficiency. Motivated by the
extremely poor performance of commonly used interpretive simulators, research
work on fast compiled instruction-set simulation was started ten years ago.
However, due to the restrictiveness of the compiled technique, it has not been
able to push through in commercial products. In this paper, we tie up with our
previous research on retargetable, compiled simulation techniques, and
provide a discussion about their benefits and limitations using a particular
compiled scheme, static scheduling, as an example. As a conclusion, we
eventually present a novel retargetable simulation technique, which combines
the performance of traditional compiled simulators with the flexibility of
interpretive simulation. This technique is not limited to any class of archi-
tectures or applications and can be utilized from architecture exploration up
to end-user software development. We demonstrate workflow and applicability of
the so-called just-in-time cache-compiled simulation technique by means of
state-of-the-art real-world architectures.

--------------------------------------------------------------------------------
ISS JIT Multicore
--------------------------------------------------------------------------------

Citation::

  @string{LCTES    = {International Conference on Languages, Compilers, Tools,
                      and Theory for Embedded Systems (LCTES)}

  @article{kyle-iss-jit-multicore-lctes2012,
    author    = {Stephen Kyle and Igor B\:{o}hm and Bj\:{o}rn Franke and
                 Hugh Leather and Nigel Topham},
    title     = {Efficiently Parallelizing Instruction Set Simulation of
                 Embedded Multi-Core Processors Using Region-based Just-in-Time
                 Dynamic Binary Translation},
    journal   = LCTES,
    month     = JUN,
    year      = {2012},
  }

ABSTRACT:

Embedded systems, as typified by modern mobile phones, are already seeing a
drive toward using multi-core processors. The number of cores will likely
increase rapidly in the future. Engineers and researchers need to be able to
simulate systems, as they are expected to be in a few generations time, running
simulations of many-core devices on today’s multi-core machines. These
requirements place heavy demands on the scalability of simulation engines, the
fastest of which have typically evolved from just-in-time (JIT) dynamic binary
translators (DBT).

Existing work aimed at parallelizing DBT simulators has focused exclusively on
trace-based DBT, wherein linear execution traces or perhaps trees thereof are
the units of translation. Regionbased DBT simulators have not received the same
attention and require different techniques than their trace-based cousins.

In this paper we develop an innovative approach to scaling multi-core, embedded
simulation through region-based DBT. We initially modify the JIT code generator
of such a simulator to emit code that does not depend on a particular thread
with its threadspecific context and is, therefore, thread-agnostic. We then
demonstrate that this thread-agnostic code generation is comparable to
thread-specific code with respect to performance, but also enables the sharing
of JIT-compiled regions between different threads. This sharing optimisation,
in turn, leads to significant performance improvements for multi-threaded
applications. In fact, our results confirm that an average of 76% of all
JIT-compiled regions can be shared between 128 threads in representative,
parallel workloads. We demonstrate that this translates into an overall
performance improvement by 1.44x on average and up to 2.40x across 12 multi-
threaded benchmarks taken from the SPLASH-2 benchmark suite, targeting our
high-performance multi-core DBT simulator for embedded ARC processors running
on a 4-core Intel host machine.

--------------------------------------------------------------------------------

Citation::

  @article{almer-iss-jit-multicore-samos2011,
    author    = {Oscar Almer and Igor B\:{o}hm and Tobias Edler von Koch and
                 Bj\:{o}rn Franke and Stephen Kyle and Volker Seeker and
                 Christopher Thompson and Nigel Topham},
    title     = {Scalable Multi-Core Simulation Using Parallel Dynamic Binary
                 Translation},
    journal   = SAMOS,
    month     = JUL,
    year      = {2011},
  }

ABSTRACT:

In recent years multi-core processors have seen broad adoption in application
domains ranging from embedded systems through general-purpose computing to
large-scale data centres. Simulation technology for multi-core systems,
however, lags behind and does not provide the simulation speed required to
effectively support design space exploration and parallel software development.
While state-of-the-art instruction set simulators (ISS) for single-core
machines reach or exceed the performance levels of speed-optimised silicon
implementations of embedded processors, the same does not hold for multi-core
simulators where large performance penalties are to be paid. In this paper we
develop a fast and scalable simulation methodology for multi-core platforms
based on parallel and just-in-time (JIT) dynamic binary translation (DBT). Our
approach can model large-scale multi-core configurations, does not rely on
prior profiling, instrumentation, or compilation, and works for all bi- naries
targeting a state-of-the-art embedded multi-core platform implementing the
ARCompact instruction set architecture (ISA). We have evaluated our parallel
simulation methodology against the industry standard SPLASH-2 and EEMBC
MULTIBENCH benchmarks and demonstrate simulation speeds up to 25,307 MIPS on a
32-core x86 host machine for as many as 2048 target processors whilst
exhibiting minimal and near constant overhead.

NOTES:

- Our main contribution is to demonstrate how to effectively apply JIT DBT in
  the context of multi-core target platforms. The key idea is to model each
  simulated processor core in a separate thread, each of which feeds work items
  for native code translation to a parallel JIT compilation task farm shared
  among all CPU threads. Combined with private first- level caches and a shared
  second-level cache for recently translated and executed native code,
  detection and elimination of duplicate work items in the translation work
  queue, and an efficient low-level implementation for atomic exchange
  operations we construct a highly scalable multi-core simulator that provides
  faster-than-FPGA simulation speeds and scales favourably up to 2048 simulated
  cores.

--------------------------------------------------------------------------------
ISS JIT
--------------------------------------------------------------------------------

Citation::

  @string{WISH     = {Workshop on Infrastructures for Software/Hardware
                      Co-Design (WISH)}}

  @article{lifshitz-isa-jit-wish2011,
    author    = {Yair Lifshitz and Robert Cohn and Inbal Livni and
                 Omer Tabach and Mark Charney and Kim Hazelwood},
    title     = {Zsim: A Fast Architectural Simulator for ISA Design-Space
                 Exploration},
    journal   = WISH,
    month     = APR,
    year      = {2011},
  }

ABSTRACT:

Moore’s law has enabled next generation CPUs to integrate more functionality
from software and peripheral logic – be it graphics, virtualization, or
encryption. As integration brings more functionality into the main core,
architecting new extensions, quantifying their impact, and validating them
becomes more complex.  One way to mitigate challenges arising from this
complexity increase is by providing simulation tools. Zsim is an x86
instruction-set simulator designed to enable rapid prototyping, evaluation,
and validation of architectural extensions. It is fast enough to execute full
platform workloads – a modern OS can boot in several minutes thus enabling
research, evaluation and validation of complex functionalities related to
multi-core configurations, virtualization, security and more. To reach such
high speeds, Zsim employs a mix between a simple just-in-time (JIT) compiler
that helps simulate simple instructions efficiently, with a fast interpreter
used for simulating new or complex instructions.  This paper presents some of
the key techniques used to optimize the Zsim interpreter for high performance,
including the use of a JIT compiler and several software caches. After
presenting an overview of the fast interpreter design, we break down the
contribution of each optimization to the overall performance, which results in
simulation speeds on the order of 100x faster than a naive implementation.

--------------------------------------------------------------------------------

Citation::

  @article{bohm-cycle-accurate-jit-isa-samos2007,
    title     = {Cycle-accurate performance modelling in an ultra-fast
                 just-in-time dynamic binary translation instruction set
                 simulator},
    author    = {Igor B\:{o}hm and Bj\:{o}rn Franke and Nigel Topham},
    journal   = SAMOS,
    month     = JUL,
    year      = {2010},
  }

ABSTRACT:

Instruction set simulators (ISS) are vital tools for compiler and processor
architecture design space exploration and verification. State-of-the-art
simulators using just-in-time (JIT) dynamic binary translation (DBT) techniques
are able to simulate complex embedded processors at speeds above 500 MIPS.
However, these functional ISS do not provide microarchitectural observability.
In contrast, low-level cycle-accurate ISS are too slow to simulate full-scale
applications, forcing developers to revert to FPGA-based simulations. In this
paper we demonstrate that it is possible to run ultra-high speed cycle-accurate
instruction set simulations surpassing FPGA-based simulation speeds. We extend
the JIT DBT engine of our ISS and augment JIT generated code with a verified
cycle-accurate processor model. Our approach can model any microarchitectural
configuration, does not rely on prior profiling, instrumentation, or
compilation, and works for all binaries targeting a state-of-the-art embedded
processor implementing the ARCompact™ instruction set architecture (ISA). We
achieve simulation speeds up to 63 MIPS on a standard ×86 desktop computer,
whilst the average cycle-count deviation is less than 1.5% for the industry
standard EEMBC and COREMARK benchmark suites.

NOTE:

JIT + Cycle-Accurate

--------------------------------------------------------------------------------

Citation::

  @article{topham-jit-isa-mobs2007,
    title     = {High Speed CPU Simulation using JIT Binary Translation},
    author    = {Nigel Topham and Daniel Jones},
    journal   = MOBS,
    month     = JUN,
    year      = {2007},
  }

ABSTRACT:

Instruction set simulators are indispensable tools for exploring the
design-space of innovative processor architec-tures, for processor
verification, and for software development. Traditional interpretive simulators
are too slow to cope with the increasing complexity of embedded processors now
being deployed in many high performance systems. High speed em- ulation
techniques based on dynamic binary translation have been proposed previously,
but thus far we have not seen flexible multi-function full-system simulators
capable of acting as golden reference models, software development platforms
and design-space exploration tools. This paper presents a target-adaptable
full-system simulator which combines the speed of JIT binary translation with
the observability of interpreted simulation. We explain the mechanisms it uses
to achieve sufficiently high performance to boot and run Linux interactively at
speeds exceeding those achievable with FPGA-based RTL emulation of the same
processor. We report performance figures from a set of representative embedded
benchmarks which range from 187 to 373 MIPS. Our results also indicate that
transient simulation speeds can exceed 1,000 MIPS, and we show that a
full-system Linux simulation can sustain more than 148 MIPS.

--------------------------------------------------------------------------------
ISS JIT-ish
--------------------------------------------------------------------------------

Citation::

  @article{reshadi-hybrid-iss-tecs2009,
    author    = {Mehrdad Reshadi and Prabhat Mishra and Nikil Dutt},
    title     = {Hybrid-compiled simulation: An efficient technique for
                 instruction-set architecture simulation},
    journal   = TECS,
    month     = APRIL,
    year      = {2009},
  }

ABSTRACT:

Instruction-set simulators are critical tools for the exploration and
validation of new processor architectures. Due to the increasing complexity of
architectures and time-to-market pressure, performance is the most important
feature of an instruction-set simulator. Interpretive simulators are flexible
but slow, whereas compiled simulators deliver speed at the cost of flexibility
and compilation overhead. This article presents a hybrid
instruction-set-compiled simulation (HISCS) technique for generation of fast
instruction-set simulators that combines the benefit of both compiled and
interpretive simulation. This article makes two important contributions: (i) it
improves the interpretive simulation performance by applying compiled
simulation at the instruction level using a novel template-customization
technique to generate optimized decoded instructions during compile time; and
(ii) it reduces the compile-time overhead by combining the benefits of both
static and dynamic-compiled simulation. Our experimental results using two
contemporary processors (ARM7 and SPARC) demonstrate an order-of-magnitude
reduction in compilation time as well as a 70% performance improvement, on
average, over the best-known published result in instruction-set simulation.

NOTES:

- proposes instruction-set compiled simulation (ICSC) moves decode to compile
  time, which also enables optimizations to the execute stage faster
- to address the compile time overhead in ISCS, a hybrid compilation technique
  leveraging compile-time static analysis and runtime dynamic analysis is used
- static component: the input program is analyzed to produce the source code of
  an optimized decoder for that particular program
- dynamic component: the decoder analyzes the input program at runtime and
  generates optimized code for the instructions as if they were statically
  compiled and optimized.


--------------------------------------------------------------------------------
ISS Decoder Generation
--------------------------------------------------------------------------------

Citation::

  @string{WBT      = {Workshop on Binary Translation (WBT)}}

  @article{krishna-software-decoder-wbt2001,
    author    = {Rajeev Krishna and Todd Austin},
    title     = {Efficient Software Decoder Design},
    journal   = WBT,
    month     = SEP,
    year      = {2001},
  }

ABSTRACT:

In this paper, we evaluate several techniques for generating and optimizing
high speed software decoders. We begin by presenting the early stages of a
new instruction set description language named ‘Rosetta’. We use specifications
written in this language to automatically generate a number of different
software decoders. We explore heuristics for generating decoder trees,
particularly with regard to enumerating “don’t care” bit positions during
evaluation in order to reduce decode tree depth and thus increase performance.
We also investigate the application of cache-conscious data placement
techniques, decoder structure, and the effects of non-contiguous bit sequences
on decoder performance. By applying these techniques to decoders produced
for the ARM and IA32 (x86) instruction sets, we are able to produce highly
flexible decoders that are comparable in size and performance to carefully
handcoded, hand-optimized decoders with substantially less programmer time
and effort.

--------------------------------------------------------------------------------

Citation::

  @article{qin-binary-decoders-dac-2003,
    author    = {Wei Qin and Sharad Malik},
    title     = {Automated Synthesis of Efficient Binary Decoders
                 for Retargetable Software Toolkits},
    journal   = DAC,
    month     = JUN,
    year      = {2003},
  }

ABSTRACT:

A binary decoder is a common component of software development tools such as
instruction set simulators, disassemblers and debuggers. The efficiency of
the decoder can have a significant impact on the efficiency of these software
tools. Automated synthesis of efficient binary decoders is therefore necessary
for retargetable software tool development frameworks targeting the rapidly
growing field of applicationspecific processor design. This paper describes a
decoder synthesis algorithm that translates a simple instruction pattern
specification into efficient binary decoders in C under given memory
constraints. The algorithm constructs a decision tree with carefully chosen
decoding primitives and cost models. As demonstrated through two case studies,
the synthesized decoders achieve efficiency comparable to hand-coded decoders
with ensured correctness. The algorithm has no limitation on the input
instruction patterns and it requires only the least amount of knowledge about
the instruction encoding. Therefore it can be used with any machine description
scheme containing instruction encoding information.

--------------------------------------------------------------------------------

Citation::

  @article{
    author    = {Nicolas Fournel and Luc Michel and
                 Fr\'{e}d\'{e}ric P\'{e}trot},
    title     = {Automated Generation of Efficient Instruction
                 Decoders for Instruction Set Simulators},
    journal   = ICCAD,
    month     = NOV,
    year      = {2013},
  }

ABSTRACT:

Fast Instruction Set Simulators (ISS) are a critical part of MPSoC design
flows. The complexity of developing these ISS combined with the ability to
extend instruction sets tend to make automated generation of ISS a need. One
important part of every ISS is its instruction decoder, but as the encoding of
instruction sets becomes less orthogonal because of the incremental addition of
instructions, the generation of a decoder is not anymore an obvious task. In
this paper, we present two automated decoder generation strategies that are
able to handle non-orthogonal instruction encodings. The first one builds a
decision tree that does not consider the instruction’s occurrences while the
second considers these frequencies. In both cases, we use binary decision
diagrams to represent the instructions encodings and the complex conditions due
to the non-orthogonality of the encodings in order to generate the decoders.
Our experiments on the MIPS and ARM (including VFP and Neon extensions)
instruction sets show that both algorithms produce efficient decoders, and that
it is beneficial to consider instruction frequencies.

--------------------------------------------------------------------------------
ISS and Compiler Auto-Generation from ADL
--------------------------------------------------------------------------------

Citation::

  @string{RAPIDO   = {Workshop on Rapid Simulation and Performance Evalution:
                      Methods and Tools (RAPIDO)}

  @article{casse-adl-iss-rapido2011,
    title     = {Fast Instruction-Accurate Simulation with SimNML},
    author    = {Hugues Cass\'{e} and Jonathan Barre and
                 Rodolphe Vaillant-David and Pascal Sainrat},
    journal   = RAPIDO,
    month     = ???,
    year      = {2011},
  }

ABSTRACT:

Instruction Level Simulation has received big attention as it allows
out-of-silicium test and hardware exploration. In this paper, we present
GLISS2, the second release of a simulator generator based on the NML ADL.
Thanks to the implementation of a set of optimization techniques (acceleration
in memory emulation, caches for the decode step and blocking of instruction
descriptors), we multiply by an average factor of 10 the simulation
performances. Additionally, although the experimentation has only been made for
the PowerPC, the performed optimization extends naturally to any instruction
set described in NML.

--------------------------------------------------------------------------------

Citation::

  @string{CASES    = {International conference on Compilers, Architecture, and
                      Synthesis for Embedded Systems (CASES)}

  @article{brandner-jit-isa-rapido2009,
    title     = {Compiler Generation from Structural Architecture Descriptions},
    author    = {Florian Brandner and Dietmar Ebner and Andreas Krall},
    journal   = CASES,
    month     = ???,
    year      = {2007},
  }

ABSTRACT:

With increasing complexity of modern embedded systems, the availability of
highly optimizing compilers becomes more and more important. At the same time,
application specific instruction-set processors (ASIPs) are used to fine-tune
hardware platforms to the intended application, demanding the availability of
retargetable components throughout the whole tool chain.
A very promising approach is to model the target architecture using a
dedicated description language that is rich enough to generate hardware
components and the required tool chain, e.g., assembler, linker, simulator, and
compiler.
In this work we present a new structural architecture description language
(ADL) that is used to derive the architecture dependent components of a
compiler backend — most notably an instruction selector based on tree pattern
matching. We combine our backend with gcc, thereby opening up the way for a
large number of readily available high level optimizations. Experimental
results show that the automatically derived code generator is competitive in
comparison to a handcrafted compiler backend.

NOTES:

- We propose a new structural ADL based on XML that is suitable for both
  automatic tool chain retargeting and hardware synthesis. Our approach follows
  a component based paradigm that enables the reuse of existing modules and is
  both extendable and comprehensible.

--------------------------------------------------------------------------------

Citation::

  @article{derrico-adl-iss-compiler-date2006,
    author    = {Joseph D'Errico and Wei Qin},
    title     = {Constructing Portable Compiled Instruction-set Simulators —-
                 An ADL-driven Approach},
    journal   = DATE,
    month     = MAR,
    year      = {2006},
  }

ABSTRACT:

Instruction set simulators are common tools used for the development of new
architectures and embedded software among countless other functions. This
paper presents a framework that quickly generates fast and flexible
instruction-set simulators from a specification based on a C-like
architecture-description language. The framework provides a consistent
platform for constructing and evaluating different classes of simulators,
including interpreters, static-compiled simulators, and dynamic-compiled
simulators. The framework also features a new construction method for
dynamic-compiled simulator that involves no low-level programming. It pro-
files and translates frequently executed regions of simulated binary to C++
code and invokes GCC to compile such code into dynamically loaded libraries,
which are then loaded into the simulator at run time to accelerate
simulation. Our experimental results based on the MIPS architecture and the
SPEC CPU2000 benchmarks show that our dynamic-compiled simulator is capable
of achieving up to 11 times speedup compared to our fast interpreter. Compared
to other dynamic-compiled simulators requiring significant system programming
expertise to construct, the proposed approach is simpler to implement and
more portable.

NOTE:

Lists three classes of Instruction Set Simulators (ISS):

- interpretive simulation:
  instructions are fetched, decoded, and executed one by one

- static-compiled simulation:
  translates the entire target binary prior to run-time,
  eliminating of fetch/decode overhead

- dynamic-compiled simulation:
  combines concepts from the first two classes; a dynamic-compiled simulator
  uses run-time code generation techniques to translate chunks of target
  binary code to host binary during execution

--------------------------------------------------------------------------------

Citation::

  @article{ceng-lisa-compiler-date2005,
    author    = {Jianjiang Ceng and Manuel Hohenauer and Rainer Leupers and
                 Gerd Ascheid and Heinrich Meyr and Gunnar Braun},
    title     = {C Compiler Retargeting Based on Instruction Semantics Models},
    journal   = DATE,
    month     = MAR,
    year      = {2005},
  }

ABSTRACT:

Efficient architecture exploration and design of application specific
instruction-set processors (ASIPs) requires retargetable software development
tools, in particular C compilers that can be quickly adapted to new
architectures. A widespread approach is to model the target architecture in a
dedicated architecture description language (ADL) and to generate the tools
automatically from the ADL specification. For C compiler generation, however,
most existing systems are limited either by the manual retargeting effort or
by redundancies in the ADL models that lead to potential inconsistencies. We
present a new approach to retargetable compilation, based on the LISA 2.0 ADL
with instruction semantics, that minimizes redundancies while simultaneously
achieving a high degree of automation. The key of our approach is to generate
the mapping rules needed in the compiler’s code selector from the instruction
semantics information. We describe the required analysis and generation
techniques, and present experimental results for several embedded processors.

--------------------------------------------------------------------------------

Citation::

  @article{ceng-adl-compiler-date2005,
    author    = {Jianjiang Ceng and Manuel Hohenauer and Rainer Leupers and
                 Gerd Ascheid and Heinrich Meyr and Gunnar Braun},
    title     = {Modeling Instruction Semantics in ADL Processor Descriptions for
                 C Compiler Retargeting},
    journal   = SAMOS,
    month     = JUL,
    year      = {2004},
  }

ABSTRACT:

Today’s Application Specific Instruction-set Processor (ASIP) design
methodology often employs centralized Architecture Description Language (ADL)
processor models, from which software tools, such as C compiler, assembler,
linker, and instruction-set simulator, can be automatically generated. Among
these tools, the C compiler is becoming more and more important. However, the
generation of C compilers requires high-level architecture information rather
than low-level details needed by simulator generation. This makes it
particularly difficult to include different aspects of the target architecture
into one single model, and meanwhile keeping consistency.  This paper presents
a modeling style, which is able to capture high and low-level architectural
information at the same time and drives both the C compiler and the simulator
generation without sacrificing the modeling flexibility. The proposed approach
has been successfully applied to model a number of contemporary, real-world
processor architectures.

--------------------------------------------------------------------------------

Citation::

  @article{hohenauer-lisa-compiler-date2004,
    author    = {Manuel Hohenauer and Hanno Scharwaechter and Kingshuk Karuri and
                 Oliver Wahlen and Tim Kogel and Rainer Leupers and
                 Gerd Ascheid and Heinrich Meyr and Gunnar Braun and
                 Hans van Someren},
    title     = {A Methodology and Tool Suite for C Compiler Generation from ADL
                 Processor Models},
    journal   = DATE,
    month     = MAR,
    year      = {2004},
  }

ABSTRACT:

Retargetable C compilers are key tools for efficient architecture exploration
for embedded processors. In this paper we describe a novel approach to
retargetable compilation based on LISA, an industrial processor modeling lan-
guage for efficient ASIP design. In order to circumvent the well-known
trade-off between flexibility and code quality in retargetable compilation, we
propose a user-guided, semiautomatic methodology that in turn builds on a
powerful existing C compiler design platform. Our approach allows to include
generated C compilers into the ASIP architecture exploration loop at an early
stage, thereby allowing for a more efficient design process and avoiding
application/architecture mismatches. We present the corresponding methodology
and tool suite and provide experimental data for two real-life embedded
processors that prove the feasibility of the approach.

--------------------------------------------------------------------------------

Citation::

  @string{ECBS-EERC = {Eastern European Conference on the Engineering
                       of Computer Based Systems (ECBS-EERC)}}

  @article{djukic-isa-sim-ecbseerc2013,
    author    = {Miodrag Djukic and Nenad Cetic and Radovan Obradovic
                 and Miroslav Popovic},
    title     = {An Approach to Instruction Set Compiled Simulator
                 Development Based on a Target Processor C Compiler
                 Back-End Design},
    journal   = ECBS-EERC,
    month     = JUN,
    year      = {2009},
  }

ABSTRACT:

Many instruction set simulation approaches place the retargetability and/or
cycle-accuracy as the key features for easier architectural exploration and
performance estimation early in the hardware development phase. This paper
describes an approach in which importance of speed and controllability is
placed above the cycle-accuracy and retargetability, thus providing a better
platform for software development. The main idea behind this work is to try to
associate the compiled simulator effort with the development of the C language
compiler for the target embedded processor, using the knowledge from that field
of work and reusing some common software elements. Through the prototype design
of a compiled simulator for the Cirrus Logic Coyote DSP architecture, many
implementation aspects are presented proving that this approach has a great
potential.

--------------------------------------------------------------------------------
Dynamic Binary Translation JIT
--------------------------------------------------------------------------------

Citation::

  @article{bohm-dbt-jit-pldi2011,
    title     = {Generalized just-in-time trace compilation using a parallel task
                 farm in a dynamic binary translator},
    author    = {Igor B\:{o}hm and Bj\:{o}rn Franke and Nigel Topham},
    journal   = PLDI,
    month     = JUN,
    year      = {2011},
  }

ABSTRACT:

Dynamic Binary Translation (DBT) is the key technology behind cross-platform
virtualization and allows software compiled for one Instruction Set
Architecture (ISA) to be executed on a processor supporting a different ISA.
Under the hood, DBT is typically implemented using Just-In-Time (JIT)
compilation of frequently executed program regions, also called traces. The
main challenge is translating frequently executed program regions as fast as
possible into highly efficient native code. As time for JIT compilation adds
to the overall execution time, the JIT compiler is often decoupled and
operates in a separate thread independent from the main simulation loop to
reduce the overhead of JIT compilation. In this paper we present two innovative
contributions. The first contribution is a generalized trace compilation
approach that considers all frequently executed paths in a program for JIT
compilation, as opposed to previous approaches where trace compilation is re-
stricted to paths through loops. The second contribution reduces JIT
compilation cost by compiling several hot traces in a concurrent task farm.
Altogether we combine generalized light-weight tracing, large translation
units, parallel JIT compilation and dynamic work scheduling to ensure timely
and efficient processing of hot traces. We have evaluated our
industry-strength, LLVM-based parallel DBT implementing the ARCompact ISA
against three benchmark suites (EEMBC, BIOPERF and SPEC CPU2006) and demon-
strate speedups of up to 2.08 on a standard quad-core Intel Xeon machine.
Across short- and long-running benchmarks our scheme is robust and never
results in a slowdown. In fact, using four processors total execution time
can be reduced by on average 11.5% over state-of-the-art decoupled, parallel
(or asynchronous) JIT compilation.

--------------------------------------------------------------------------------

Citation::

  @string{HIPEAC   = {Int'l Conf. on High Performance Embedded Architectures
                      and Compilers (HiPEAC)}}

  @article{jones-ltu-dbt-hipeac2009,
    title     = {High Speed CPU Simulation Using LTU Dynamic Binary Translation},
    author    = {Daniel Jones and Nigel Topham},
    journal   = HIPEAC,
    month     = JAN,
    year      = {2009},
  }

ABSTRACT:

In order to increase the speed of dynamic binary translation based simulators
we consider the translation of large translation units consisting of multiple
blocks. In contrast to other simulators, which translate hot blocks or pages,
the techniques presented in this paper profile the target program’s execution
path at runtime. The identification of hot paths ensures that only executed
code is translated whilst at the same time offering greater scope for
optimization. Mean performance figures for the functional simulation of EEMBC
benchmarks show the new simulation techniques to be at least 63% faster than
basic block based dynamic binary translation.

NOTES:

- This paper is concerned with that class of simulator which provides accurate
  and observable modelling of the entire processor state. This is possible to
  achieve by operating at the register transfer level, but such simulators are
  very slow.
- In contrast, compiled simulation, which can be many orders of magnitude
  faster, does not have the same degree of observability and can only be used
  in situations where the application code is known in advance and is available
  in source form. Programs which require an operating system or which are
  shrink-wrapped can not benefit from compiled simulation.
- Dynamic Binary Translation (DBT) on the other hand combines interpretive and
  compiled simulation techniques in order to maintain high speed, observ-
  ability and flexibility. However, achieving accurate state observability
  remains in tension with high speed simulation.
- Typically, in DBT simulators, the unit of translation is either the target
  instruction or the basic block. By increasing the size of the
  translation-unit it is possible to achieve significant speedups in simulation
  performance.


--------------------------------------------------------------------------------
Multicore ISS
--------------------------------------------------------------------------------

An Accurate Multi-processing Simulator Based on ADL
- http://ieeexplore.ieee.org/xpl/abstractCitations.jsp?arnumber=4690760&tag=1

Scalable Instruction Set Simulator for Thousand-core Architectures
Running on GPGPUs
- http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=5547092

Ocelot: A Dynamic Compiler for Bulk-Synchronous Applications in Heterogeneous
Systems
- http://gpuocelot.gatech.edu/publications/ocelot-a-dynamic-compiler-for-bulk-synchronous-applications-in-heterogeneous-systems/



