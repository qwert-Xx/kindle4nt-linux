/* SPDX-License-Identifier: GPL-2.0-or-later */
/* Host register/comparator model: search and non-applying restore contract.
 * Not a substitute for ARM CPU/cache/self-refresh hardware execution. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include "zqcal-config.h"
struct model { uint32_t ctl73, ctl74, ctl75; unsigned pu, edge, reads, writes;
               int absent_pu, absent_pd; };
static unsigned compare(struct model *m, unsigned p, unsigned d, int pd)
{
 m->ctl74 = ((d + 1) << 24) | ((p + 1) << 16) | (pd ? 16 : 0);
 m->ctl75 = (d << 8) | p;
 m->ctl73 = 0x10000;
 m->writes += 3;
 unsigned r = pd ? (m->absent_pd || d < m->edge) :
                       (!m->absent_pu && p >= m->pu);
 m->reads++;
 m->ctl73 = 0;
 m->writes++;
 return r;
}
static int measure(struct model *m, unsigned *pu, unsigned *pd)
{
 uint32_t a = m->ctl73, b = m->ctl74, c = m->ctl75;
 unsigned p, d;
 int status = 0;
 for (p = 0; p < 32 && !compare(m, p, 0, 0); p++);
 if (p == 32) { status = -34; goto restore; }
 for (d = 0; d < 15 && compare(m, p, d, 1); d++);
 if (!d || d == 15 || p == 31) { status = -34; goto restore; }
 *pu = p; *pd = d - 1; /* SPL increments then subtracts two. */
restore:
 m->ctl73 = 0; m->ctl74 = b; m->ctl75 = c; m->ctl73 = a;
 assert(m->ctl73 == a && m->ctl74 == b && m->ctl75 == c);
 assert(m->reads <= 47);
 return status;
}
int main(void)
{
 unsigned cases = 0, pu, pd;
 for (unsigned p = 0; p < 31; p++) for (unsigned d = 1; d < 15; d++) {
  struct model m = { .ctl73=0x200000, .ctl74=0x9180010, .ctl75=0x817,
                     .pu=p, .edge=d };
  assert(!measure(&m, &pu, &pd)); assert(pu == p && pd == d - 1);
  assert(((k4_zq_config74(pu, pd) >> 16) & 31) == pu + 1);
  assert(((k4_zq_config74(pu, pd) >> 24) & 15) == pd + 1);
  cases++;
 }
 for (unsigned f = 0; f < 4; f++) {
  struct model m = { .ctl73=0x200000, .ctl74=0x5090010, .ctl75=0x408,
                    .pu=f == 3 ? 31 : 8, .edge=f == 2 ? 0 : 5,
                    .absent_pu=f == 0, .absent_pd=f == 1 };
  assert(measure(&m, &pu, &pd) == -34); cases++;
 }
 assert(k4_zq_config74(8, 4) == 0x05090000);
 assert(k4_zq_config74(23, 8) == 0x09180000);
 for (unsigned stage = 0; stage < 3; stage++)
  for (unsigned fault = 0; fault < 8; fault++) {
   int status = fault & 1 ? -34 : 0;
   unsigned checks = k4_zq_checks(stage, status, !(fault & 2), !(fault & 4));
   assert((k4_zq_checked_status(status, checks) == 0) == (stage == 2 && !fault));
   cases++;
  }
 for (unsigned n = 0; n <= 129; n++) for (unsigned done = 0; done <= 130; done++) {
  assert(k4_zq_log_valid(0x5a514331, n, done) == (n && n <= 128 && done <= n));
  assert(!k4_zq_log_valid(0, n, done));
  cases++;
 }
 printf("PASS %u register-model cases, stock/static encodings, bounded search and restore\n", cases);
}
