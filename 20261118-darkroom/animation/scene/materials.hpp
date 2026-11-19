#pragma once
enum Pattern { Plain,Plaster,Tile,Wood,Paint,Grain,Brushed,Porcelain,Cloth,Paper,Picture,Negative,Dial,Sticker,Water,Floor,Fluting,Film,Screen,Card,Drapery,FullImage,ClearWater,Flock,MufflerWool,Yarn,BlackGlass,Oak,WasherGlass,WaterGlass,Mesh,BlackoutCotton,BubbleFilm };
struct Mat{V base;float rough=.5f,mirror=0;Pattern kind=Plain;int image=0;V emit{};float ratio=1;bool hanging=false;};
std::vector<Mat> mats;
int mat(V col,float rough=.62f,float refl=0,Pattern t=Plain,int im=0,V emission={}){mats.push_back({col,rough,refl,t,im,emission});return mats.size()-1;}
std::array<Pic,14> plates;
constexpr std::array<int,4> filmFrames{0,12,1,12};
int wall,tile,wood,frameWood,black,iron,charcoal,steel,polished,chrome,copper,brass,cream,grey,redEnamel,vinyl,amber,ivory,liquid,linen,baseFloor,ceramic,lum,safelens,rubber,palePaper,negative,clockFace,whiteLight,offwhite,oxide,glazed,metalRack,coffee,ventDark,film,screen,card,brown,mark,glint;
int pics[4],stickers[6],sheets[4];
V lensPos{12,161,145},projX{1,0,0},projY{0,1,0};
constexpr float paperLevel=91.55f;
constexpr float projWidth=37.3f,projDepth=28.3f;
void materials(){
 wall=mat({.55,.48,.43},.91,0,Plaster);tile=mat({.68,.74,.69},.35,.075,Tile);
 wood=mat({.37,.25,.16},.56,.035,Wood);frameWood=mat({.57,.35,.16},.6,.012,Wood);
 black=mat({.038,.045,.061},.49,.08,Paint);iron=mat({.104,.12,.145},.44,.13,Paint);
 charcoal=mat({.072,.068,.079},.72,.019,Grain);steel=mat({.32,.34,.36},.36,.28,Brushed);
 polished=mat({.43,.46,.45},.245,.48,Brushed);chrome=mat({.35,.38,.39},.18,.68,Brushed);
 copper=mat({.48,.28,.20},.46,.19,Brushed);brass=mat({.52,.36,.18},.38,.20,Brushed);
 cream=mat({.72,.68,.54},.47,.055,Paint);grey=mat({.39,.45,.43},.49,.09,Paint);
 redEnamel=mat({.51,.115,.075},.36,.13,Paint);vinyl=mat({.049,.041,.055},.6,.02,Grain);
 amber=mat({.24,.105,.04},.19,.48,Plain);ivory=mat({.72,.65,.53},.4,.085,Porcelain);
 liquid=mat({.028,.034,.041},.12,.43,Water);linen=mat({.77,.69,.59},.95,0,Cloth);
 baseFloor=mat({.18,.19,.20},.76,.035,Floor);ceramic=mat({.73,.70,.60},.31,.12,Porcelain);
 lum=mat({.45,.075,.025},.3,0,Screen,0,{3.8,.31,.065});
 safelens=mat({.65,.06,.016},.26,.05,Screen,0,{1.45,.075,.021});
 rubber=mat({.043,.036,.045},.66,.02,Grain);palePaper=mat({.87,.82,.70},.84,.025,Paper);
 negative=mat({.23,.12,.105},.42,.08,Negative);clockFace=mat({.74,.74,.62},.57,.035,Dial,3);
 whiteLight=mat({.9,.88,.75},.16,.08,Plain,0,{2.3,2.13,1.63});
 offwhite=mat({.81,.78,.69},.62,.04,Paint);oxide=mat({.20,.075,.045},.88,0,Grain);
 glazed=mat({.23,.35,.36},.34,.12,Paint);metalRack=mat({.38,.41,.43},.3,.32,Brushed);
 coffee=mat({.24,.16,.105},.64,.015,Wood);ventDark=mat({.019,.022,.036},.91,0,Plain);
 film=mat({.28,.14,.09},.33,.12,Film);screen=mat({.28,.28,.24},.85,0,Plain);
 card=mat({.49,.40,.30},.85,.01,Card);brown=mat({.30,.17,.12},.66,.01,Wood);
 mark=mat({.09,.065,.072},.82,0);glint=mat({.81,.73,.57},.32,.22);
 for(int i=0;i<4;i++){int plate=i==3?12:i;
  pics[i]=mat({.94,.89,.80},.67,.018,Picture,plate);sheets[i]=mat({.90,.84,.72},.61,.035,Picture,plate);
 }
 for(int i=0;i<6;i++)stickers[i]=mat({.78,.72,.58},.79,.014,Sticker,4+i);
}
struct Surface{V base,emit,n;float rough,mirror;};
V rippleOrigin{-32,47,82.3f};
// Water height in the washer's own horizontal coordinates.
const Frame washerPose=turn({-89.4f,176.7f,88.87f},-9.0f);
constexpr float washerLevel=30.80f;
float washerWave(float x,float y){
 float dx=x+19.0f,dy=y-7.1f,d=std::hypot(dx,dy);
 return .149f*std::sin(.749f*d-.47f)*std::exp(-d/37.f)
   +.141f*std::sin(.32f*x+.61f*y+.80f*std::sin(x*.141f)+.16f)
   +.078f*std::sin(.48f*x-.47f*y+.47f*std::sin(y*.19f));
}
bool washerBoundary(Pattern k){return k==WasherGlass||k==WaterGlass;}
// The old sealer is smoother on the high ridges of the benchtop grain.
float varnishRoughness(V p){
 float grain=noise(p.x*.032f,p.y*.15f,182);
 return .29f+.11f*grain;
}
Surface surface(int m,V p,V n,float u,float v){
 const Mat&t=mats[m];V color=t.base,normal=n,em=t.emit;float rough=t.rough,refl=t.mirror;
 float a=std::abs(n.x)>.82f?p.y:p.x,b=std::abs(n.z)>.76f?p.y:p.z;
 float f=noise(a*.075f,b*.075f,87),g=noise(a*.37f,b*.37f,23);
 switch(t.kind){
 case Plaster:{
  float fine=noise(a*.89f,b*.89f,3),chips=step(.72f,.83f,noise(a*.12f,b*.16f,13)+.21f*noise(a*.47f,b*.47f,7));
  float wet=step(.42f,.88f,noise(a*.055f,b*.019f,67))*.22f;
  float oldPaint=step(.58f,.82f,noise(a*.041f,b*.019f,44)+.14f*g);
  color=color*(.94f+.12f*f+.037f*(g-.5f)+.030f*(fine-.5f)-wet*.48f-.08f*chips-.105f*oldPaint);
  if(p.y>217&&p.x<-39)color=color*.83f;
  break;}
 case Tile:{
  float A=a/15.3f,B=(b-38)/15.3f;
  float da=std::min(fract(A),1-fract(A))*15.3f,db=std::min(fract(B),1-fract(B))*15.3f;
  float edge=std::min(da,db),j=hash(std::floor(A),std::floor(B),9);
  color=color*(.88f+.18f*j+.046f*g);
  if(edge<.34f){float mortar=step(.04f,.34f,edge);color=mix(V{.22,.21,.22},color,.16f+.84f*mortar);refl*=.5f;}
  else if(edge<.60f)color=color*(1+.1f*(1-step(.34f,.60f,edge)));
  float drip=step(.75f,.90f,noise(a*.47f,b*.019f,15)+.05f*g)*(.34f+.66f*g);
  float damp=step(.55f,.84f,noise(a*.058f,b*.026f,91)+.14f*drip)*(1-step(100,151,b));
  color=color*(1-.17f*drip-.068f*damp);
  if(p.y>216&&p.x<-39)color=color*.70f;
  rough=.46f-.20f*damp;
  if(edge>.35f){
   V horizontal=std::abs(n.x)>.82f?V{0,1,0}:V{1,0,0};
   float cupped=.015f+.009f*j;
   normal=norm(n+horizontal*(cupped*std::sin(2*PI*A)) + V{0,0,cupped*std::sin(2*PI*B)});
  }
  break;}
 case BlackGlass:{
  float reed=std::sin(p.y*2.15f+.085f*p.z+.39f*std::sin(p.z*.055f));
  float insideSash=1-step(159.4f,162.4f,p.z);
  normal=norm(n+V{0,.093f*insideSash*reed+.021f*std::sin(p.y*.080f+p.z*.031f),
                     .020f*std::sin(p.z*.078f-p.y*.041f)});
  float dust=step(.61f,.90f,noise(p.y*.108f,p.z*.058f,271)+.12f*g);
  color=color*(.77f+.26f*noise(p.y*.028f,p.z*.032f,251)+.15f*dust);
  rough=.22f+.12f*dust;break;}
 case Oak:{
  float transverse=n.z>.65f?p.y:p.z;
  float grain=noise(p.x*.023f,transverse*.28f,62),sweep=.67f*(grain-.5f)+.34f*std::sin(p.x*.057f);
  float line=.5f+.5f*std::sin(transverse*2.12f+sweep*4.1f+noise(p.x*.09f,transverse*.19f,61));
  float pores=step(.72f,.89f,noise(p.x*.066f,transverse*2.2f,70));
  color=color*(.73f+.24f*grain+.16f*line-.14f*pores+.06f*g);
  if(n.z>.92f&&p.z>86.2f&&p.z<86.66f)rough=varnishRoughness(p);
  if(n.z>.82f&&p.z>86.2f&&p.z<86.66f&&p.x<-21.f&&p.x>-57.f){
   for(V ring:std::array<V,2>{{{-45.2f,162.7f,5.08f},{-47.6f,165.9f,5.48f}}}){
    float x=p.x-ring.x,y=p.y-ring.y;
    float edge=std::abs(std::hypot(x,y)-ring.z-.126f*std::sin(x*.65f+y*.17f));
    float dried=(1-step(.15f,.48f,edge))*step(.24f,.62f,g+.16f*std::sin(x*.81f+y*.23f));
    color=mix(color,V{.53f,.412f,.306f},dried*.63f);
   }
  }
  if(p.y<151&&p.z>80)color=color*(1+.18f*(1-step(.2f,1.85f,std::abs(p.z-84.65f))));
  break;}
 case Mesh:{
  float thread=std::min(std::abs(fract(p.x*1.25f)-.5f),std::abs(fract(p.y*1.25f)-.5f));
  color=color*mix(.48f,.89f,step(.14f,.30f,thread));break;}
 case Floor:{
  float A=(p.x+20)/22,B=(p.y+10)/22,dx=std::min(fract(A),1-fract(A)),dy=std::min(fract(B),1-fract(B));
  color=color*(.77f+.27f*hash(std::floor(A),std::floor(B),4)+.12f*g);
  if(std::min(dx,dy)<.015f)color=color*.51f;
  break;}
 case Wood:{float wave=std::sin((b+.65f*noise(a*.018f,b*.017f,2))*.81f+2.8f*noise(a*.028f,b*.16f));
  color=color*(.77f+.14f*wave+.16f*noise(a*.07f,b*.48f,4)+.1f*f);
  if(n.z>.80f&&p.z>86.15f&&p.z<86.7f&&p.y>148&&p.y<215){
   for(V ring:std::array<V,2>{V{-47.1f,162.2f,5.8f},V{-49.7f,166.5f,6.1f}}){
    float x=p.x-ring.x,y=p.y-ring.y,r=std::sqrt(x*x+y*y);
    float chalk=1-step(.085f,.40f,std::abs(r-ring.z-.12f*std::sin(x)));
    color=color*(1+.37f*chalk*step(.22f,.67f,g+.22f*std::cos(x*.6f)));
   }
  }break;}
 case Paint:color=color*(.90f+.13f*f+.045f*g);break;
 case Brushed:color=color*(.89f+.13f*f+.055f*noise(a*.10f,b*1.7f));break;
 case Grain:case Porcelain:case Card:color=color*(.91f+.13f*f+.026f*g);break;
 case BlackoutCotton:{
  // Worn blackout twill. Fine yarn stays within a single value family.
  float staple=noise(p.x*1.23f+p.y*.27f,p.z*.77f,124);
  float weft=noise(p.x*.15f,p.z*.47f+p.x*.06f,37);
  color=color*(.942f+.075f*staple+.04f*weft);
  break;}
 case Drapery:{
  float weave=.57f*noise(a*.31f,b*.36f,52)+.43f*noise(a*.85f,b*.10f,18);
  color=color*(.885f+.16f*weave);
  float hem=std::min(v*90,(1-v)*90);if(hem<.65f)color=color*.76f;break;}
 case FullImage:color=color*(.026f+.974f*plates[t.image].get(u,v));break;
 case Paper:color=color*(.96f+.045f*g);break;
 case MufflerWool:{
  float x=u*24.f,y=v*t.ratio,end=std::min(y,t.ratio-y);
  auto band=[](float t,float a,float b){return step(a-.115f,a+.115f,t)*(1-step(b-.115f,b+.115f,t));};
  // A dark yarn and an oat yarn make a visibly woven check. Every stripe
  // follows the same length and width coordinate through all the folds.
  float offset=fract((y+.95f)/15.8f)*15.8f;
  float warp=band(x,3.70f,8.65f)+band(x,17.6f,20.75f);
  float weft=band(offset,5.85f,10.1f);
  V ground{.53f,.335f,.262f},burgundy{.052f,.044f,.069f},oat{.89f,.74f,.57f};
  V wool=ground*(1-.71f*warp)*(1-.68f*weft)+burgundy*(.38f*warp+.35f*weft);
  float pin=band(x,9.13f,10.26f)+band(x,15.69f,16.34f);
  float pinY=band(offset,3.11f,4.60f)+.78f*band(offset,10.75f,11.46f);
  wool=mix(wool,oat,sat(.85f*pin+.82f*pinY)*(1-.34f*weft)*(1-.33f*warp));
  float cream=band(end,3.25f,6.43f)+.90f*band(end,7.74f,9.02f);
  wool=mix(wool,oat,cream*(.97f-.15f*warp));
  wool=mix(wool,burgundy,.92f*band(end,6.50f,7.57f));
  float twill=std::cos(2*PI*(x*1.54f+(fract(x*.25f)<.5f?1:-1)*y*1.19f));
  color=wool*(.941f+.093f*noise(x*1.8f,y*1.2f,666)+.037f*twill);break;}
 case Yarn:color=color*(.93f+.11f*g);break;
 case Cloth:{
  float heddle=fract(u*8.4f+.07f*std::sin(v*11+u));
  float stripe=heddle<.022f?.70f:1.f;
  if((v>.793f&&v<.824f)||(v>.862f&&v<.878f)||v>.983f)stripe*=.27f;
  float absorbed=.71f+.29f*step(.10f,.53f,v+.09f*std::sin(8*u)+.10f*f);
  color=color*(stripe*absorbed*(.86f+.08f*std::sin(u*744)+.045f*std::sin(v*607)+.12f*g));
  break;}
 case Picture:{
  float margin=.064f,mx=.055f;float uu=(u-mx)/(1-2*mx),vv=(v-margin)/(1-margin-.105f);
  float density=1.f;if(uu>=0&&uu<1&&vv>=0&&vv<1){
   float aspect=t.ratio*(1-2*mx)/(1-margin-.105f),native=float(plates[t.image].w)/plates[t.image].h;
   if(aspect<native)uu=.5f+(uu-.5f)*aspect/native;else vv=.5f+(vv-.5f)*native/aspect;
   density=.013f+.975f*std::pow(plates[t.image].get(uu,vv),1.58f);
  }
  else if(v>.925f&&v<.951f&&u>.68f&&u<.87f){
   float l=fract(u*87+std::sin(v*240)*.32f);if(l>.78f&&noise(u*75,v*370,11)>.48f)density=.36f;
  }
  color=color*density;break;}
 case Dial:{
  float ink=plates[t.image].get(u,v);color=color*(.020f+.91f*ink);
  // Phosphorescent seconds marks on the mechanical darkroom timer.
  float phosphor=step(.48f,.86f,ink);em+=V{.093f,.244f,.183f}*phosphor;
  break;}
 case Sticker:color=color*(.018f+.98f*plates[t.image].get(u,v));break;
 case Negative:color=color*(.54f+.39f*g);break;
 case Film:{float x=fract(u*4.3f),y=v;if(y>.12f&&y<.88f&&x>.04f&&x<.95f){
  float d=plates[filmFrames[int(u*4.3f)%4]].get(x,(y-.12f)/.76f);color=color*(1.48f-1.21f*d);
 }else color=color*(.52f+.21f*g);break;}
 // The moving jet carries its refraction corrugations in its actual geometry.
 case ClearWater:break;
 case Water:color=color*(.88f+.14f*f);break;
 case Screen:{
  float X=(u-.5f)*2,Y=(v-.5f)*2,r2=X*X+Y*Y;
  // The bulb is slightly off centre behind the pressed red glass. The
  // narrower hot core leaves a band of deep amber visible inside the lip.
  float bx=X+.13f,by=Y+.11f;
  float core=std::exp(-3.35f*(bx*bx+1.19f*by*by));
  float shoulder=std::exp(-1.49f*(bx*bx+1.42f*by*by));
  float ribs=.85f+.15f*std::cos(2*PI*(v*10.4f+.43f*X*X+.13f*X));
  float rim=1-.53f*step(.63f,1.f,r2);
  V glass{.79f+3.15f*shoulder+3.85f*core,
          .047f+.16f*shoulder+.61f*core*core,
          .016f+.039f*shoulder+.157f*core*core};
  em=glass*(rim*ribs*(.92f+.13f*f));
  break;}
 default:break;
 }
 return {color,em,normal,rough,refl};
}
