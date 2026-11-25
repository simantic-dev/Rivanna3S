// Host-side decoder: reads "<t> <id-hex> <data hex bytes...>" lines on stdin and prints the
// signals by name using the team's own cantools-generated Common/can_structs.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rivanna3_s.h"
#include "bps.h"
#include "mppt.h"
int main(void){ char l[256]; while(fgets(l,sizeof l,stdin)){ double t; unsigned id; int off; if(sscanf(l,"%lf %x%n",&t,&id,&off)<2) continue;
 uint8_t d[8]={0}; int n=0; char*p=l+off; unsigned b; int c; while(n<8&&sscanf(p," %x%n",&b,&c)==1){d[n++]=b;p+=c;}
 printf("%.6f 0x%X ",t,id);
 if(id==0x258){struct rivanna3_s_precharge_status_t m; rivanna3_s_precharge_status_unpack(&m,d,n); printf("PrechargeStatus motor_stage=%u mppt_stage=%u cont12_fault=%u other_fault=%u threshold=%u cont12=%u hal_motor=%u hal_mppt=%u\n",m.motor_stage,m.mppt_stage,m.cont12_fault,m.other_fault,m.threshold,m.cont12,m.hal_effect_motor,m.hal_effect_mppt);}
 else if(id==0x406){struct bps_bps_status_t m; bps_bps_status_unpack(&m,d,n); printf("BpsStatus pack_voltage=%.1f pack_current=%.1f soc=%.1f discharge_relay=%u charge_relay=%u\n",m.pack_voltage*0.1,m.pack_current*0.1,m.pack_soc*0.5,m.discharge_relay_status,m.charge_relay_status);}
 else if(id==0x3AA){printf("BpsError raw=%02X%02X%02X%02X\n",d[0],d[1],d[2],d[3]);}
 else if(id==0xC8){struct rivanna3_s_motor_commands_t m; rivanna3_s_motor_commands_unpack(&m,d,n); printf("MotorCommands regen_braking=%u cruise_speed=%u throttle=%u manual=%u regen=%u cruise=%u\n",m.regen_braking,m.cruise_speed,m.throttle,m.manual_drive,m.regen_drive,m.cruise_drive);}
 else if(id==0x1F4){struct rivanna3_s_pedal_status_t m; rivanna3_s_pedal_status_unpack(&m,d,n); printf("PedalStatus throttle_pedal=%u brake_pedal=%u\n",m.throttle_pedal,m.brake_pedal);}
 else if(id==0x180||id==0x181){struct mppt_mg0_status_t m; mppt_mg0_status_unpack(&m,d,n); printf("MG%d_Status input_current=%.2f input_voltage=%.2f\n",id&1,m.mg0_input_current,m.mg0_input_voltage);}
 else if(id==0x280||id==0x281){struct mppt_mg0_output_voltage_input_power_t m; mppt_mg0_output_voltage_input_power_unpack(&m,d,n); printf("MG%d_OutputVoltage_InputPower output_voltage=%.2f input_power=%.2f\n",id&1,m.mg0_output_voltage,m.mg0_input_power);}
 else if(id==0x480||id==0x481){struct mppt_mg0_pcbmosfet_temperature_t m; mppt_mg0_pcbmosfet_temperature_unpack(&m,d,n); printf("MG%d_Temperature pcb=%.2f mosfet=%.2f\n",id&1,m.mg0_pcb_temperature*0.01,m.mg0_mosfet_temperature*0.01);}
 else printf("raw\n"); } return 0; }
