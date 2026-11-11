# Power check (read-only, nothing changed)

Checked 2026-11-05 21:04:33 while the run was active (end of stage C).

| Item | Value |
|---|---|
| Active power plan (`powercfg /getactivescheme`) | 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c (High performance). Already High performance, so no change was made. |
| Power limit: current / default / minimum / maximum | 300.00 W / 300.00 W / 100.00 W / 300.00 W (requested 300.00 W). No graphics card limit was changed. |
| Power draw | average 296.45 W, instantaneous 279.15 W; 2.46 s sample: min 90.35 W, average 289.64 W, max 441.56 W |
| Performance state | P2 |
| Clock event (throttle) reasons now | SW Power Cap: Active. Idle, HW Slowdown, HW Thermal Slowdown, HW Power Brake, SW Thermal Slowdown, Sync Boost, Board Limit, Reliability, Display and Applications clock settings: Not Active |
| Clock event counters since the driver started | SW Power Capping 25,263.7 s (about 7.0 h); SW Thermal Slowdown 0 s; HW Thermal Slowdown 0 s; HW Power Braking 0 s; Sync Boost 0 s |
| Clocks now / maximum | Graphics and SM 1440 / 2100 MHz; Memory 7601 / 8001 MHz; Video 1260 / 1950 MHz |

**Reading:** the card is held at its 300 W board power limit, which is also its default and maximum, so under full load the clocks settle below their maximum (SM 1440 of 2100 MHz). This is the normal power cap of an RTX A6000, not overheating: the thermal slowdown and power-brake counters are zero. The power plan was already High performance, and nothing was changed.

## Raw output

```
powercfg /getactivescheme
Power Scheme GUID: 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  (High performance)

nvidia-smi -q -d POWER,PERFORMANCE,CLOCK
==============NVSMI LOG==============

Timestamp                                              : Thu Nov  5 21:04:33 2026
Driver Version                                         : 621.14 [Deprecated; will be removed in CUDA 14.0. Use KMD Version instead]
CUDA Version                                           : 13.5 [Deprecated; will be removed in CUDA 14.0. Use CUDA UMD Version instead]
KMD Version                                            : 621.14
CUDA UMD Version                                       : 13.5

Attached GPUs                                          : 1
GPU 00000000:41:00.0
    Performance State                                  : P2
    Clocks Event Reasons
        Idle                                           : Not Active
        Applications Clocks Setting                    : Not Active
        SW Power Cap                                   : Active
        HW Slowdown                                    : Not Active
            HW Thermal Slowdown                        : Not Active
            HW Power Brake Slowdown                    : Not Active
        Sync Boost                                     : Not Active
        SW Thermal Slowdown                            : Not Active
        Display Clock Setting                          : Not Active
        Board Limit                                    : Not Active
        Reliability                                    : Not Active
    Clocks Event Reasons Counters
        SW Power Capping                               : 25263652060 us
        Sync Boost                                     : 0 us
        SW Thermal Slowdown                            : 0 us
        HW Thermal Slowdown                            : 0 us
        HW Power Braking                               : 0 us
    Sparse Operation Mode                              : N/A
    GPU Power Readings
        Average Power Draw                             : 296.45 W
        Instantaneous Power Draw                       : 279.15 W
        GPU Ceiling Power Limit
            Current Power Limit                        : 300.00 W
            Requested Power Limit                      : 300.00 W
            Default Power Limit                        : 300.00 W
        GPU Base Power
            Current Base Power                         : N/A
            Requested Base Power                       : N/A
            Default Base Power                         : N/A
        Min Power Limit                                : 100.00 W
        Max Power Limit                                : 300.00 W
    Power Samples
        Duration                                       : 2.46 sec
        Number of Samples                              : 119
        Max                                            : 441.56 W
        Min                                            : 90.35 W
        Avg                                            : 289.64 W
    GPU Memory Power Readings 
        Average Power Draw                             : N/A
        Instantaneous Power Draw                       : N/A
    Module Power Readings
        Average Power Draw                             : N/A
        Instantaneous Power Draw                       : N/A
        Current Power Limit                            : N/A
        Requested Power Limit                          : N/A
        Default Power Limit                            : N/A
        Min Power Limit                                : N/A
        Max Power Limit                                : N/A
    EDPp Multiplier                                    : N/A
    Clocks
        Graphics                                       : 1440 MHz
        SM                                             : 1440 MHz
        Memory                                         : 7601 MHz
        Video                                          : 1260 MHz
    Applications Clocks
        Graphics                                       : Requested functionality has been deprecated
        Memory                                         : Requested functionality has been deprecated
    Default Applications Clocks
        Graphics                                       : Requested functionality has been deprecated
        Memory                                         : Requested functionality has been deprecated
    Deferred Clocks
        Memory                                         : N/A
    Max Clocks
        Graphics                                       : 2100 MHz
        SM                                             : 2100 MHz
        Memory                                         : 8001 MHz
        Video                                          : 1950 MHz
    Max Customer Boost Clocks
        Graphics                                       : N/A
    SM Clock Samples
        Duration                                       : Not Found
        Number of Samples                              : Not Found
        Max                                            : Not Found
        Min                                            : Not Found
        Avg                                            : Not Found
    Memory Clock Samples
        Duration                                       : Not Found
        Number of Samples                              : Not Found
        Max                                            : Not Found
        Min                                            : Not Found
        Avg                                            : Not Found
    Clock Policy
        Auto Boost                                     : N/A
        Auto Boost Default                             : N/A
    DLA Clocks
        Engine                                         : N/A
        Max Engine                                     : N/A
```
