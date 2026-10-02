/* SPDX-License-Identifier: GPL-2.0-or-later */
#include <assert.h>
#include <stdio.h>
#include "zqcal-config.h"
int main(void)
{
 unsigned int pu,pd,checks,stage,errors,n=0;
 for(pu=0;pu<=30;pu++)for(pd=0;pd<=14;pd++){
  unsigned int c74=k4_zq_config74(pu,pd)|16,c75=(pd<<8)|pu;
  assert(k4_zq_baseline_valid(0x200000,c74,c75)); n++;
  assert(!k4_zq_baseline_valid(0x310000,c74,c75)); n++;
  assert(!k4_zq_baseline_valid(0x200000,c74^16,c75)); n++;
  for(checks=0;checks<8;checks++)for(stage=0;stage<5;stage++)for(errors=0;errors<2;errors++){
   int v=k4_zq_apply_status(0,stage,errors,checks,pu,pd,0x200000,c74,c75);
   assert((v==0)==(stage==3 && errors==0 && checks==7));n++;
   assert(k4_zq_apply_status(-110,stage,errors,checks,pu,pd,0x200000,c74,c75)==-110);n++;
  }
  assert(k4_zq_apply_status(0,3,0,7,pu,pd,0x200000,c74^16,c75)<0);n++;
 }
 assert(!k4_zq_baseline_valid(0x200000,0x10200010,0xf1f));n++;
 assert(k4_zq_config74(8,4)==0x05090000);n++;
 assert(k4_zq_config74(23,8)==0x09180000);n++;
 printf("APPLY_C_CHECKS_PASS %u cases\n",n);
 return 0;
}
