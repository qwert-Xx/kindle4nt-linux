/* SPDX-License-Identifier: GPL-2.0-only */
#ifndef K4_ZQCAL_CONFIG_H
#define K4_ZQCAL_CONFIG_H
/* The shipped LPDDR1 SPL uses +1 fields, despite the RM's M1 labels. */
static inline unsigned int k4_zq_config74(unsigned int pu, unsigned int pd)
{
 return ((pd + 1) << 24) | ((pu + 1) << 16);
}
/* Shared by the command and host fault tests. */
static inline unsigned int k4_zq_checks(unsigned int stage, int status,
                                       int memory_ok, int registers_ok)
{
 return (stage == 2 && status == 0 ? 1U : 0U) |
        (memory_ok ? 2U : 0U) | (registers_ok ? 4U : 0U);
}
static inline int k4_zq_checked_status(int status, unsigned int checks)
{
 return status ? status : checks == 7 ? 0 : -5;
}
static inline int k4_zq_log_valid(unsigned int magic, unsigned int n, unsigned int done)
{
 return magic == 0x5a514331 && n > 0 && n <= 128 && done <= n;
}
/* A runtime diagnostic must be able to reload the recorded baseline. */
static inline int k4_zq_baseline_valid(unsigned int c73, unsigned int c74,
                                     unsigned int c75)
{
 unsigned int pu = c75 & 31, pd = (c75 >> 8) & 15;
 return pu <= 30 && pd <= 14 && c75 == ((pd << 8) | pu) &&
        c73 == 0x200000 && c74 == (k4_zq_config74(pu, pd) | 16);
}
static inline int k4_zq_apply_status(int status, unsigned int stage,
                                    unsigned int errors, unsigned int checks,
                                    unsigned int pu, unsigned int pd,
                                    unsigned int c73, unsigned int c74,
                                    unsigned int c75)
{
 if (status) return status;
 return stage == 3 && !errors && checks == 7 && pu <= 30 && pd <= 14 &&
        c73 == 0x200000 && c74 == (k4_zq_config74(pu, pd) | 16) &&
        c75 == ((pd << 8) | pu) ? 0 : -5;
}
#endif
