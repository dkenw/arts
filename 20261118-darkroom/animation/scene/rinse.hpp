#pragma once

// The nozzle, water, floating stock, and light paths share coordinates in cm.
namespace rinse {
constexpr float period=7.2f, level=82.25f, nozzleZ=120.34f;
constexpr float paperW=39.f,paperH=29.7f,angle=-17.5f;
constexpr float jetSpeed=100.f,nozzleRadius=.49f,gravity=981.f;
int jetMaterial=-1,bubbleMaterial=-1;
float time=0,omega=0,impactPhase=0,impactX=0,impactY=0;
float paperX=-56,paperY=44.9f,paperCos=1,paperSin=0,paperLift=0,rollX=0,rollY=0;
float travel(float drop){return (std::sqrt(jetSpeed*jetSpeed+2*gravity*drop)-jetSpeed)/gravity;}
float phase(float t){return 2*PI*t/period;}
float inlet(float p){return .59f*std::sin(3*p+.64f)+.27f*std::sin(7*p-1.4f)+.14f*std::sin(11*p+.2f);}
// A tilt at the lip gives the thread a small horizontal launch velocity.
// Each parcel retains its sideways momentum as gravity accelerates its fall.
V jetAxis(float drop,float release){
 float age=travel(drop);
 float vx=4.2f+1.24f*std::sin(4*release+.36f)+1.48f*std::sin(31*release+.6f*std::sin(5*release));
 float vy=-.45f+.81f*std::sin(5*release-.90f)+.85f*std::cos(31*release+.42f);
 return {-32.f+age*vx,47.f+age*vy,nozzleZ-drop};
}
// Capillary disturbances can travel upstream relative to the falling water.
// Integrate their downstream speed along the accelerating column.
float surfaceTravel(float drop){
 constexpr float slip=43.f;
 float speed=std::sqrt(jetSpeed*jetSpeed+2*gravity*drop);
 return (speed-jetSpeed+slip*std::log((speed-slip)/(jetSpeed-slip)))/gravity;
}
void setTime(float t){
 time=t;omega=phase(t);
 impactPhase=phase(t-travel(nozzleZ-level));
 V landing=jetAxis(nozzleZ-level,impactPhase);impactX=landing.x;impactY=landing.y;
 // The wet sheet drifts around a small circulation cell. Its yaw and
 // heave lag the lateral drift. The outlined edge and its water film share
 // this pose, including where the curled corner breaks the surface.
 float drift=omega+.19f*std::sin(omega-.58f)-.058f*std::sin(2*omega+.29f);
 paperX=-56.f+.81f*std::sin(drift-.08f)+.075f*std::sin(2*drift+.45f);
 paperY=44.9f+.39f*std::sin(drift-.91f)+.13f*std::cos(2*drift-.39f);
 float yaw=rad(angle+.44f*std::sin(drift-.93f)+.095f*std::sin(2*drift+.49f));
 paperCos=std::cos(yaw);paperSin=std::sin(yaw);
 paperLift=.032f*std::sin(2*omega-.65f)+.016f*std::cos(3*omega+.84f);
 rollX=.00145f*std::cos(2*omega-.58f)+.00065f*std::sin(3*omega+.51f);
 rollY=.0016f*std::sin(2*omega+.24f);
}
float paperHeight(float u,float v){
 return 82.054f+paperLift+rollX*(u-.5f)*paperW+rollY*(.5f-v)*paperH+
    (1.376f+.027f*std::sin(3*omega-.9f))*std::pow(u,4.4f)*(1-v)*(1-v)
    +.155f*std::sin(u*4.25f+v*.8f);
}
V sheet(float u,float v){
 float x=(u-.5f)*paperW,y=(.5f-v)*paperH;
 return {paperX+x*paperCos-y*paperSin,paperY+x*paperSin+y*paperCos,paperHeight(u,v)};
}
float height(float x,float y){
 float dx=x-impactX,dy=y-impactY,d=std::sqrt(dx*dx+dy*dy+.012f);
 float c=dx/(d+.16f),s=dy/(d+.16f);
 // Long fronts expand from the impact. Evaluate the source at the time
 // a disturbance left the tap, so a single crest travels across the bath.
 float r=d*(1+.022f*s+.018f*(c*c-s*s))+.48f*s*std::sin(.12f*d+.45f);
 constexpr float waveSpeed=17.5f;
 float emitted=impactPhase-phase(r/waveSpeed);
 float group=.5f+.5f*std::cos(3*emitted+.61f*std::sin(2*emitted-.77f)+.21f*c);
 float packet=.43f+.57f*group*group;
 float train=-11*emitted+.46f*std::sin(3*emitted+.47f)+.22f*std::sin(2*emitted-1.4f);
 float crest=train+.17f*s+.17f*std::sin(.15f*d+2*c);
 float spread=step(.50f,1.92f,d)*std::exp(-d/45.f)/std::sqrt(1+.048f*d);
 float outward=spread*((.305f*packet+.058f)*(std::sin(crest)+.22f*std::sin(2*crest-.82f))
                   +(.036f+.019f*group)*std::sin(1.04f*r-21*impactPhase-.41f*c)
                   +.035f*std::sin(.31f*r-6*impactPhase+.45f*c*s));
 // The steel walls send back a softer, delayed front. Two paths meet on
 // the open side of the photograph and break up the red reflection there.
 auto echo=[&](float imageY,float shift){
  float ey=y-imageY,dist=std::hypot(dx,ey);
  float past=impactPhase-phase(dist/waveSpeed);
  float envelope=.64f+.36f*std::cos(3*past-.4f);
  return .037f*envelope*std::exp(-dist/36.f)*std::sin(-11*past+shift+.25f*dx/(dist+.3f));
 };
 float returns=echo(2*18.1f-impactY,1.2f)+echo(2*73.9f-impactY,-.61f);
 float bottomWash=.0045f*std::sin(.15f*x+.25f*y-5*impactPhase);
 float pulse=inlet(impactPhase);
 float dist=(d-(.96f+.07f*pulse+.09f*c*s))/.44f;
 float impact=-(.224f+.027f*pulse)*std::exp(-d*d/.45f)
              +(.097f+.024f*pulse)*std::exp(-dist*dist);
 // A submerged print damps the short waves and makes a meniscus at its curled edge.
 float sx=x-paperX,sy=y-paperY,u=.5f+(sx*paperCos+sy*paperSin)/paperW;
 float v=.5f-(-sx*paperSin+sy*paperCos)/paperH;
 float ex=(std::abs(u-.5f)-.5f)*paperW,ey=(std::abs(v-.5f)-.5f)*paperH;
 float outside=std::hypot(std::max(ex,0.f),std::max(ey,0.f))+std::min(std::max(ex,ey),0.f);
 float damp=mix(.21f,1.f,step(-2.f,4.7f,outside)),meniscus=0;
 if(std::abs(outside)<2.7f)meniscus=.165f*step(-.18f,.16f,paperHeight(sat(u),sat(v))-level)*std::exp(-std::abs(outside)/.55f);
 // The soaked stock lifts the film on its face a fraction of a millimetre.
 float localLift=.70f*(1-step(-1.7f,2.4f,outside))*
       (paperLift+rollX*(u-.5f)*paperW+rollY*(.5f-v)*paperH);
 return level+localLift+(outward+returns+bottomWash)*damp+impact+meniscus
       +.125f*std::exp(-std::max(0.f,28.15f-std::abs(y-46.f))/.33f);
}
V waterSurface(float u,float v){
 constexpr float hw=67.95f,hh=28.15f,r=5.2f;
 float localY=(2*v-1)*hh,corner=std::max(0.f,std::abs(localY)-hh+r);
 float halfWidth=hw-r+std::sqrt(std::max(0.f,r*r-corner*corner));
 float x=-53.5f+(2*u-1)*halfWidth,y=localY+46.f;
 return {x,y,height(x,y)};
}
V jet(float u,float v){
 float drop=(nozzleZ-level+1.50f)*v,release=phase(time-travel(drop)),a=2*PI*u;
 V center=jetAxis(drop,release);
 // The average radius retains the still's gravity taper. The material
 // release and the surface-wave release are different physical clocks.
 float speed=std::sqrt(jetSpeed*jetSpeed+2*gravity*drop);
 float radius=nozzleRadius*std::sqrt(jetSpeed/speed);
 float surfacePhase=phase(time-surfaceTravel(drop));
 float wave=43*surfacePhase+.73f*std::sin(5*surfacePhase-.23f)+.28f*std::sin(11*surfacePhase+.84f);
 float envelope=.67f+.33f*std::sin(4*surfacePhase+.68f);
 // The lower filament develops necks and shoulders while the inlet stays
 // attached. Normalizing the mean square keeps the average flow narrow.
 float amplitude=(.095f+.27f*v)*envelope;
 float neck=amplitude*(std::sin(wave)+.27f*std::sin(2*wave-.70f));
 neck+=(.021f+.042f*v)*std::sin(58*surfacePhase+.54f*std::sin(7*surfacePhase));
 float flute=(.024f+.023f*v)*std::sin(3*a+.56f*std::cos(wave)-.61f);
 float r=radius*(1+neck)*(1+flute)/std::sqrt(1+.536f*amplitude*amplitude);
 // Stretched sections form a small ribbon. Its opposite faces transmit a
 // clear window onto the room; the rounded shoulders bend that same light.
 // The stadium section has area pi*r*r, including both rounded edges.
 float window=step(-.38f,.53f,-std::sin(wave));
 float flat=(.18f+.82f*v)*(.07f+1.33f*window);
 float minor=r/(1+flat);
 float side=.25f*PI*(r*r-minor*minor)/minor;
 float yaw=.81f+.28f*std::sin(6*release-.15f)+.48f*std::sin(wave-.81f);
 float ca=std::abs(std::cos(a-yaw)),sa=std::abs(std::sin(a-yaw));
 float edge=minor/std::max(sa,.0001f);
 if(edge*ca>side)edge=side*ca+std::sqrt(std::max(0.f,minor*minor-side*side*sa*sa));
 return center+V{edge*std::cos(a),edge*std::sin(a),0};
}
// The short optical path through this clear thread admits very little scatter.
float airInStream(V p,float incidence){
 float drop=std::clamp(nozzleZ-p.z,0.f,nozzleZ-level+1.5f);
 float t=phase(time-travel(drop)),v=drop/(nozzleZ-level);
 V c=jetAxis(drop,t);
 float angle=std::atan2(p.y-c.y,p.x-c.x);
 // A little air carried from the spout catches the lamp for only a short
 // portion of a parcel's fall. Clear stretches transmit the room behind.
 float packet=.5f+.5f*std::cos(32*t+.78f*std::sin(5*t+.23f)+.28f*std::cos(angle-.4f));
 float bright=packet*packet*packet;
 return (.002f+(.016f+.072f*v)*bright)*(.55f+.45f*incidence);
}
float impactAir(V p){
 float d=std::hypot(p.x-impactX,p.y-impactY);
 return .009f*std::exp(-d*d/.43f)*(.78f+.22f*std::cos(5*impactPhase));
}
void movingGeometry(){
 patch(204,94,waterSurface,liquid);
 patch(32,23,sheet,sheets[3]);
 patch(24,68,jet,jetMaterial);
}
}  // namespace rinse
