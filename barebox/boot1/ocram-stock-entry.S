/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Stock ROM stack/return ABI, frozen USB register sequence in compact records. */
.syntax unified
.arm
.section .entry,"ax"
.global _start, plugin_entry
_start:
 b plugin_entry
plugin_entry:
 push {r0-r6,r8,lr}
 cmp r0,#0xf8000000
 mov r4,r0
 ldr r3,=0x70020000
 strhi r3,[r0]
 ldr r3,=IMAGE_SIZE
 strhi r3,[r1]
 mov r3,#0x42c
 strhi r3,[r2]
 ldr r8,=0xf8008080
 ldr r3,=0x4b34504c
 str r3,[r8]
 mov r3,#1
 str r3,[r8,#4]
 ldr r5,=table_before
 ldr r6,=table_before_end
 bl execute_rows
 cmp r0,#0
 beq failed
 ldr r5,=table_after
 ldr r6,=table_after_end
 bl execute_rows
 cmp r0,#0
 beq failed
 mov r3,#2
 str r3,[r8,#4]
 /* Match stock: output arguments written first, SI_REV 11 vs other revision. */
 mov r0,#0x48
 ldr r1,[r0]
 cmp r1,#0x11
 adr r0,destination
 adr r1,copy_size
 adr r2,copy_bootdata
 mov r3,#0x2a00
 addeq r3,r3,#0xad
 addne r3,r3,#0x19
 /* Stock leaves these ROM registers intact when calling its helper. */
 ldr r5,[sp,#20]
 ldr r6,[sp,#24]
 ldr r8,[sp,#28]
 cmp r4,#0xf8000000
 blxhi r3
 ldr r2,=0xf8008080
 str r0,[r2,#12]
 mov r3,#4
 str r3,[r2,#4]
 dsb sy
 pop {r0-r6,r8,lr}
 mov r0,#1
 bx lr
failed:
 mov r3,#0xe1
 str r3,[r8,#4]
 dsb sy
 pop {r0-r6,r8,lr}
 mov r0,#0
 bx lr
execute_rows:
 cmp r5,r6
 moveq r0,#1
 bxeq lr
 str r5,[r8,#8]
 ldmia r5!,{r0,r1}
 and r2,r0,#3
 bic r0,r0,#3
 cmp r2,#0
 streq r1,[r0]
 dsb sy
 beq execute_rows
 mov r3,#0x100000
1:
 cmp r2,#1
 ldrbeq r12,[r0]
 ldrne r12,[r0]
 and r12,r12,r1
 cmp r2,#2
 beq 2f
 cmp r12,#0
 bne execute_rows
 b 3f
2:
 cmp r12,#0
 beq execute_rows
3:
 subs r3,r3,#1
 bne 1b
 mov r0,#0
 bx lr
.align 2
destination: .word 0x70020000
copy_size: .word IMAGE_SIZE
copy_bootdata: .word 0x70020000, IMAGE_SIZE, 0
.ltorg
.section .table_before,"a"
.global table_before,table_before_end
table_before:
#include "before.inc"
table_before_end:
.section .table_after,"a"
.global table_after,table_after_end
table_after:
#include "after.inc"
table_after_end:
