/* SPDX-License-Identifier: GPL-2.0-or-later */
/* K4 NT only. Cache traversal derived from ocram-imx50-cache.S and the original
 * mx50_suspend.S (Copyright 2010-2012 Amazon.com, Inc.).
 * Calibration search matches boot0 SPL f80085a4, LPDDR1 argument 1.
 * Default: comparator only. Explicit -a diagnostic loads then rolls back
 * entirely in OCRAM before returning to DDR-resident C code.
 */
#include <linux/linkage.h>
.text
.arm
.arch armv7-a
.balign 32
.global k4_zq_sram_start, k4_zq_sram_end
k4_zq_sram_start:
 push {r4-r11, r12, lr}
 mov r8, sp
 mov sp, r1
 mov r12, r0
 str r8, [r12, #0]
 mrs r0, cpsr
 str r0, [r12, #4]
 cpsid if
 mrc p15, 0, r0, c1, c0, 0
 str r0, [r12, #8]
 mrc p15, 0, r1, c1, c0, 1
 str r1, [r12, #12]
 mrc p15, 2, r1, c0, c0, 0
 str r1, [r12, #16]
 bic r0, r0, #(1 << 2)
 bic r0, r0, #(1 << 11)
 bic r0, r0, #(1 << 12)
 mcr p15, 0, r0, c1, c0, 0
 isb
	mrc	p15, 1, r0, c0, c0, 1
	str	r0, [r12, #36]
	ands	r3, r0, #0x7000000
	mov	r3, r3, lsr #23
	mov	r6, #0
	beq	.Lcache_clean_done
	mov	r10, #0
.Lcache_level:
	add	r2, r10, r10, lsr #1
	mov	r1, r0, lsr r2
	and	r1, r1, #7
	cmp	r1, #2
	blt	.Lcache_next
	mcr	p15, 2, r10, c0, c0, 0
	isb
	mrc	p15, 1, r1, c0, c0, 0
	and	r2, r1, #7
	add	r2, r2, #4
	ubfx	r4, r1, #3, #10
	clz	r5, r4
	ubfx	r7, r1, #13, #15
.Lcache_set:
	mov	r9, r4
.Lcache_way:
	orr	r11, r10, r9, lsl r5
	orr	r11, r11, r7, lsl r2
	mcr	p15, 0, r11, c7, c14, 2
	add	r6, r6, #1
	subs	r9, r9, #1
	bge	.Lcache_way
	subs	r7, r7, #1
	bge	.Lcache_set
.Lcache_next:
	add	r10, r10, #2
	cmp	r3, r10
	bgt	.Lcache_level
.Lcache_clean_done:
	dsb

 ldr r0, [r12, #12]
 bic r0, r0, #2
 mcr p15, 0, r0, c1, c0, 1
 ldr r0, [r12, #8]
 bic r0, r0, #1
 bic r0, r0, #4
 bic r0, r0, #(1 << 11)
 bic r0, r0, #(1 << 12)
 dsb
 mcr p15, 0, r0, c1, c0, 0
 isb
 /* All addresses are physical identity addresses from here. */
 mov r6, #0x14000000
 ldr r4, [r6, #0x4c]
 ldr r5, [r6, #0x50]
 str r4, [r12, #20]
 str r5, [r12, #24]
 mov r7, #0
 ldr r0, [r6]
 tst r0, #1
 beq .Lpark
 tst r4, #1
 bne .Lpark
 bic r0, r5, #31
 str r0, [r6, #0x50]
 dsb
 ldr r1, [r6, #0x50]
 cmp r0, r1
 bne .Lentry_fail
 mov r2, #0x100000
.Lready:
 ldr r0, [r6, #0xfc]
 tst r0, #(1 << 16)
 beq .Lready_retry
 ldr r1, [r6, #0x13c]
 tst r1, #(1 << 8)
 beq .Lrequest
.Lready_retry:
 subs r2, r2, #1
 bne .Lready
 b .Lentry_fail
.Lrequest:
 mov r2, #256
.Lgap:
 subs r2, r2, #1
 bne .Lgap
 orr r0, r4, #1
 str r0, [r6, #0x4c]
 dsb
 mov r2, #0x100000
.Llow:
 ldr r0, [r6, #0xfc]
 tst r0, #(1 << 16)
 beq .Lmeasure
 subs r2, r2, #1
 bne .Llow
 b .Lentry_fail
.Lmeasure:
 mov r0, #1
 str r0, [r12, #40] /* self-refresh reached */
 ldr r0, [r6, #0x124]
 str r0, [r12, #28]
 ldr r0, [r6, #0x128]
 str r0, [r12, #32]
 ldr r0, [r6, #0x12c]
 str r0, [r12, #36]
 ldr r0, [r12, #56]
 cmp r0, #1
 beq .Lapply
 mov r1, #0
.Lpu:
 cmp r1, #32
 beq .Lno_edge
 add r0, r1, #1
 mov r0, r0, lsl #16
 orr r0, r0, #(1 << 24)
 str r0, [r6, #0x128]
 str r1, [r6, #0x12c]
 bl .Lcompare
 cmp r0, #1
 beq .Lpu_found
 add r1, r1, #1
 b .Lpu
.Lpu_found:
 str r1, [r12, #44]
 mov r2, #0
.Lpd:
 cmp r2, #15
 beq .Lno_edge
 add r0, r2, #1
 mov r0, r0, lsl #24
 add r3, r1, #1
 orr r0, r0, r3, lsl #16
 orr r0, r0, #16
 str r0, [r6, #0x128]
 orr r0, r1, r2, lsl #8
 str r0, [r6, #0x12c]
 bl .Lcompare
 cmp r0, #0
 beq .Lpd_found
 add r2, r2, #1
 b .Lpd
.Lpd_found:
 /* Stock post-loop r2-2: candidate+1-2 = candidate-1. */
 cmp r2, #0
 beq .Lno_edge
 sub r2, r2, #1
 str r2, [r12, #48]
 b .Lrestore_zq
.Lno_edge:
 mvn r7, #33 /* -ERANGE, never recommend a saturated search. */
 b .Lrestore_zq /* Default failure must never fall into explicit apply. */
.Lapply:
 ldr r1, [r12, #60]
 ldr r2, [r12, #64]
 str r1, [r12, #44]
 str r2, [r12, #48]
 orr r0, r1, r2, lsl #8
 str r0, [r6, #0x12c]
 add r1, r1, #1
 add r2, r2, #1
 mov r0, r2, lsl #24
 orr r0, r0, r1, lsl #16
 bl k4_zq_load_pair
 mov r0, #1
 str r0, [r12, #84]
 ldr r0, [r6, #0x124]
 str r0, [r12, #88]
 ldr r0, [r6, #0x128]
 str r0, [r12, #92]
 ldr r0, [r6, #0x12c]
 str r0, [r12, #96]
 b .Lexit
.Lrestore_zq:
 /* Do NOT pulse SW_LOAD; active pad buffers remain untouched. */
 mov r0, #0
 str r0, [r6, #0x124]
 ldr r0, [r12, #32]
 str r0, [r6, #0x128]
 ldr r0, [r12, #36]
 str r0, [r6, #0x12c]
 ldr r0, [r12, #28]
 str r0, [r6, #0x124]
 dsb
 b .Lexit
.Lentry_fail:
 mvn r7, #4
.Lexit:
 str r4, [r6, #0x4c]
 dsb
 mov r2, #0x100000
.Lhigh:
 ldr r0, [r6, #0xfc]
 tst r0, #(1 << 16)
 beq .Lhigh_retry
 ldr r1, [r6, #0x13c]
 tst r1, #(1 << 8)
 bne .Lhigh_retry
 ldr r3, [r6, #0x264]
 tst r3, #1
 bne .Lrestore
.Lhigh_retry:
 subs r2, r2, #1
 bne .Lhigh
 b .Lpark
.Lrestore:
 ldr r0, [r12, #56]
 cmp r0, #1
 bne .Lrestore_cpu
 ldr r0, [r12, #84]
 cmp r0, #1
 bne .Lrestore_cpu
 /* DDR is accessible again; compare allocated 16MiB from OCRAM, with
  * caches/MMU still off. Never execute C with the candidate pad codes. */
 mov r0, #2
 str r0, [r12, #84]
 ldr r8, [r12, #72]
 ldr r9, [r12, #76]
 mov r10, #0
 movw r11, #0x79b9
 movt r11, #0x9e37
.Ltest_candidate:
 cmp r10, r9
 beq .Lrollback_entry
 mul r0, r10, r11
 movw r1, #0x37e9
 movt r1, #0xa51c
 eor r0, r0, r1
 ldr r1, [r8, r10, lsl #2]
 cmp r0, r1
 beq .Ltest_next
 mvn r7, #4
 ldr r0, [r12, #80]
 add r0, r0, #1
 str r0, [r12, #80]
.Ltest_next:
 add r10, r10, #1
 movw r0, #2047
 tst r10, r0
 bleq .Lfeed
 b .Ltest_candidate
.Lrollback_entry:
 /* Re-enter SR, reload both saved pad codes, exit and verify safety. */
 mov r2, #0x100000
.Lrollback_ready:
 ldr r0, [r6, #0xfc]
 tst r0, #(1 << 16)
 beq .Lrollback_retry
 ldr r1, [r6, #0x13c]
 tst r1, #(1 << 8)
 beq .Lrollback_request
.Lrollback_retry:
 subs r2, r2, #1
 bne .Lrollback_ready
 b .Lpark
.Lrollback_request:
 mov r2, #256
.Lrollback_gap:
 subs r2, r2, #1
 bne .Lrollback_gap
 orr r0, r4, #1
 str r0, [r6, #0x4c]
 dsb
 mov r2, #0x100000
.Lrollback_low:
 ldr r0, [r6, #0xfc]
 tst r0, #(1 << 16)
 beq .Lrollback_load
 subs r2, r2, #1
 bne .Lrollback_low
 b .Lpark
.Lrollback_load:
 ldr r0, [r12, #36]
 str r0, [r6, #0x12c]
 ldr r0, [r12, #32]
 bic r0, r0, #16
 bl k4_zq_load_pair
 /* Registers are restored as well, after both active buffers reload. */
 ldr r0, [r12, #32]
 str r0, [r6, #0x128]
 ldr r0, [r12, #28]
 str r0, [r6, #0x124]
 dsb
 mov r0, #3
 str r0, [r12, #84]
 b .Lexit
.Lrestore_cpu:
 mov r2, #256
.Lexit_gap:
 subs r2, r2, #1
 bne .Lexit_gap
 str r5, [r6, #0x50]
 dsb
 ldr r0, [r6, #0x4c]
 cmp r0, r4
 bne .Lpark
 ldr r0, [r6, #0x50]
 cmp r0, r5
 bne .Lpark
 str r7, [r12, #52]
 mov r0, #2
 str r0, [r12, #40]
 mov r0, #0
 mcr p15, 0, r0, c7, c5, 0
 mcr p15, 0, r0, c7, c5, 6
 ldr r0, [r12, #16]
 mcr p15, 2, r0, c0, c0, 0
 ldr r0, [r12, #12]
 mcr p15, 0, r0, c1, c0, 1
 ldr r0, [r12, #8]
 dsb
 mcr p15, 0, r0, c1, c0, 0
 isb
 ldr r0, [r12, #4]
 msr cpsr_c, r0
 ldr sp, [r12, #0]
 pop {r4-r11, r12, pc}
.Lpark:
 mvn r0, #109
 str r0, [r12, #52]
 dsb
 b .Lpark /* DDR cannot be trusted; watchdog/manual recovery only. */
/* r0 contains CTL74 PU selection; the SPL has no final-load delay. */
k4_zq_load_pair:
 str r0, [r6, #0x128]
 mov r1, #0x310000
 str r1, [r6, #0x124]
 mov r2, #0x200000
 str r2, [r6, #0x124]
 orr r0, r0, #16
 str r0, [r6, #0x128]
 str r1, [r6, #0x124]
 str r2, [r6, #0x124]
 dsb
 bx lr
.Lfeed:
 movw r3, #0x8002
 movt r3, #0x53f9
 movw r0, #0x5555
 strh r0, [r3]
 movw r0, #0xaaaa
 strh r0, [r3]
 dsb
 bx lr
.Lcompare:
 movw r3, #0x8002
 movt r3, #0x53f9
 movw r0, #0x5555
 strh r0, [r3]
 movw r0, #0xaaaa
 strh r0, [r3]
 dsb
 mov r0, #0x10000
 str r0, [r6, #0x124]
 dsb
 mov r3, #0
.Ldelay:
 add r3, r3, #1
 cmp r3, #4096
 bne .Ldelay
 ldr r0, [r6, #0x14c]
 and r0, r0, #1
 mov r3, #0
 str r3, [r6, #0x124]
 dsb
 bx lr
k4_zq_sram_end:
