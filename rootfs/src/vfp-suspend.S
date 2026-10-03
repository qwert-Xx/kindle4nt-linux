/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Load all D registers, perform write(fd, "mem\n", 4), capture before C resumes. */
	.syntax unified
	.arch armv7-a
	.fpu neon
	.arm
	.text
	.align 2
	.global k4_vfp_suspend
	.type k4_vfp_suspend, %function
k4_vfp_suspend:
	push {r4-r8, lr}
	vpush {d8-d15}
	mov r4, r2
	vmrs r6, fpscr
	ldr r3, [r1, #256]
	vmsr fpscr, r3
	vldmia r1!, {d0-d15}
	vldmia r1!, {d16-d31}
	adr r1, .Lmem
	mov r2, #4
	mov r7, #4 /* ARM EABI __NR_write; no libc between load and capture. */
	svc #0
	mov r5, r0
	vstmia r4!, {d0-d15}
	vstmia r4!, {d16-d31}
	vmrs r0, fpscr
	str r0, [r4]
	vmsr fpscr, r6
	vpop {d8-d15}
	mov r0, r5
	pop {r4-r8, pc}
.Lmem:
	.ascii "mem\n"
	.size k4_vfp_suspend, .-k4_vfp_suspend
	.section .note.GNU-stack,"",%progbits
