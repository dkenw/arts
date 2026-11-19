#pragma once

// Centimetres. The rest grid is a rectangle cut on the grain. We hang it at
// its clip positions, then let gravity act on its warp, weft and bias.
namespace dark_cloth {
constexpr int nx=36,ny=36;
constexpr float rodY=203.15f,rodZ=190.55f;
int index(int col,int row){return col+row*(nx+1);}
struct Link { int a,b;float length,strength; };
struct Sheet {
 std::vector<V> p,previous;
 std::vector<float> mobility;
 std::vector<Link> links;
 std::vector<std::array<float,4>> reach;
 std::array<V,4> anchors{};
 explicit Sheet(bool left):p((nx+1)*(ny+1)),previous(p.size()),mobility(p.size(),1.f),reach(p.size()){
  std::array<float,4> clips=left?std::array<float,4>{{-66.1f,-51.85f,-36.15f,-21.7f}}:
                                 std::array<float,4>{{-18.6f,-1.9f,15.26f,32.35f}};
  float cutWidth=left?57.8f:56.1f,cutHeight=left?82.6f:81.9f;
  for(int i=0;i<4;i++)anchors[i]={clips[i],rodY-.45f+.18f*std::sin(i*1.75f),
      rodZ-8.4f+.35f*std::sin(i*2.21f+.62f*left)};
  for(int row=0;row<=ny;row++)for(int col=0;col<=nx;col++){
   int k=index(col,row);float u=float(col)/nx,v=float(row)/ny;
   int span=std::min(col/12,2);float local=(col-span*12)/12.f;
   V top=mix(anchors[span],anchors[span+1],local);
   float phase=2*PI*((left?2.25f:1.67f)*u+.065f*std::sin(4.7f*v+3.1f*u)+.08f*v*(u-.4f));
   p[k]={top.x+.69f*v*std::sin(7.5f*u),top.y-3.15f*std::sin(phase)-.91f*std::sin(PI*u),
         top.z-cutHeight*v-1.21f*std::sin(local*PI)*(1-v)};
   for(int j=0;j<4;j++)reach[k][j]=std::hypot((col-12*j)*cutWidth/nx,row*cutHeight/ny)*1.003f;
  }
  for(int i=0;i<4;i++){int k=index(12*i,0);p[k]=anchors[i];mobility[k]=0;}
  // A 3 cm piece of twill tape holds the left panel. Its cross-section
  // folds inside the loop. An uneven gather leaves the far corner a little shorter.
  std::vector<int> held;
  std::vector<V> freePositions,gatherPositions;
  if(left){
   for(int i=0;i<=nx;i+=2){
    float u=float(i)/nx;
    int bandRow=20+int(std::round(4.f*u+.46f*std::sin(2*PI*u-.31f)));
    int k=index(i,bandRow);
    float wave=2*PI*(2.84f*u+.12f+.061f*std::sin(2*PI*u-.47f));
    V cinched{-65.5f+15.4f*(u+.024f*std::sin(2*PI*u)),202.72f+4.12f*std::sin(wave)+.27f*std::cos(PI*u),
              145.3f-2.25f*u+.29f*std::sin(wave)};
    held.push_back(k);freePositions.push_back(p[k]);gatherPositions.push_back(cinched);
    mobility[k]=0;
   }
  }
  for(int j=0;j<=ny;j++)for(int i=0;i<=nx;i++){
   auto connect=[&](int dx,int dy,float strength){
    int x=i+dx,y=j+dy;if(x<0||x>nx||y<0||y>ny)return;
    links.push_back({index(i,j),index(x,y),std::hypot(dx*cutWidth/nx,dy*cutHeight/ny),strength});
   };
   connect(1,0,.97f);connect(0,1,.97f);connect(1,1,.74f);connect(-1,1,.74f);
   connect(2,0,.165f);connect(0,2,.22f);
   connect(3,0,.062f);connect(0,3,.075f);
  }
  previous=p;
  for(int tick=0;tick<230;tick++){
   float draw=step(8.f,137.f,float(tick));
   for(size_t j=0;j<held.size();j++)p[held[j]]=mix(freePositions[j],gatherPositions[j],draw);
   for(size_t k=0;k<p.size();k++)if(mobility[k]){
    V at=p[k],velocity=(p[k]-previous[k])*(tick<152?.947f:.885f);
    p[k]+=velocity+V{0,0,-.119f};previous[k]=at;
   }
   for(int iter=0;iter<15;iter++){
    bool reverse=(tick+iter)&1;
    for(size_t j=0;j<links.size();j++){
     const Link& e=links[reverse?links.size()-1-j:j];V direction=p[e.b]-p[e.a];
     float a=mobility[e.a],b=mobility[e.b],w=a+b,distance=len(direction);
     if(w==0||distance<.0001f)continue;
     V correction=direction*((distance-e.length)*e.strength/(w*distance));
     p[e.a]+=correction*a;p[e.b]+=correction*(-b);
    }
    if((iter&3)==3){
     // A pinned heading limits the geodesic reach of each patch of cloth.
     for(size_t k=0;k<p.size();k++)if(mobility[k]){
      for(int j=0;j<4;j++){V delta=p[k]-anchors[j];float distance=len(delta);
       if(distance>reach[k][j])p[k]=anchors[j]+delta*(reach[k][j]/distance);}
      p[k].y=std::min(p[k].y,214.0f);
     }
    }
   }
  }
 }
 static V cubic(V a,V b,V c,V d,float t){
  return b+(c-a)*(.5f*t)+(a*2.f-b*5.f+c*4.f-d)*(.5f*t*t)
     +(-a+b*3.f-c*3.f+d)*(.5f*t*t*t);
 }
 V point(float u,float v)const{
  float x=sat(u)*nx,y=sat(v)*ny;int i=std::min(int(x),nx-1),j=std::min(int(y),ny-1);
  auto read=[&](int a,int b){return p[index(std::clamp(a,0,nx),std::clamp(b,0,ny))];};
  V rows[4];for(int k=0;k<4;k++)rows[k]=cubic(read(i-1,j+k-1),read(i,j+k-1),
       read(i+1,j+k-1),read(i+2,j+k-1),x-i);
  return cubic(rows[0],rows[1],rows[2],rows[3],y-j);
 }
 V front(float u,float v)const{
  V a=point(u+.001f,v)-point(u-.001f,v),b=point(u,v+.001f)-point(u,v-.001f);
  V normal=norm(cross(b,a));return normal;
 }
};

void rail(int ironwork,int burnished){
 // The short side brackets clear the wall and leave a strip of plain plaster
 // visible through the eight rings above the sewn heading.
 for(float x:{-68.25f,37.9f}){
  V mounting{x,217.84f,rodZ+.21f};
  lathe(mounting,{0,-1,0},{{0,2.28f,ironwork},{.49f,2.31f,ironwork},{.68f,2.02f,ironwork}},24);
  for(int j:{-1,1})screw(mounting+V{1.40f*j,-.69f,.68f*j},{0,-1,0},.34f);
  tube({mounting+V{0,-.55f,0},{x,211.8f,rodZ+.13f},{x,205.4f,rodZ+.08f},{x,rodY,rodZ+.06f}},.68f,ironwork,10,3);
 }
 rod({-71.15f,rodY,rodZ},{40.9f,rodY,rodZ},.91f,ironwork,20);
 for(float x:{-71.11f,40.78f})oval({x,rodY,rodZ},{1.10f,1.25f,1.25f},burnished,16,10);
}
void clip(V anchor,int number,int oxide,int metal){
 float lean=.54f+.15f*std::sin(number*1.77f);
 V side=norm(V{lean,.84f,.036f*std::cos(number*2.51f)}),up=norm(V{-.02f,0,1});
 float cz=rodZ+.79f-2.95f+.30f;
 V centre{anchor.x,rodY,cz};
 std::vector<V> loop;
 for(int j=0;j<=40;j++){
  float a=2*PI*j/40;loop.push_back(centre+side*(2.72f*std::cos(a))+up*(2.95f*std::sin(a)));
 }
 tube(loop,.35f,metal,9,1);
 V bottom=centre-up*2.95f;V foot=anchor+V{0,-.10f,-.74f};
 tube({bottom,bottom+V{-.10f,-.13f,-.76f},foot+V{0,0,2.10f}},.28f,oxide,8,2);
 box(foot+V{0,.12f,.97f},{1.63f,.83f,2.19f},oxide,.23f);
 rod(foot+V{-.83f,-.37f,1.35f},foot+V{.83f,-.37f,1.35f},.18f,metal,7);
}

void keeper(int tape,int boundEdge,int fitting){
 // One utility tieback runs from a small wall hook, around the gathered
 // cloth, and back to the same hook. Gravity gives the leading edge a dip.
 const std::vector<V> c{{-66.7f,214.2f,145.82f},{-66.7f,207.8f,145.65f},{-66.9f,201.7f,145.31f},
     {-66.45f,198.3f,145.05f},{-63.2f,197.64f,144.02f},{-57.4f,197.60f,142.83f},
     {-52.4f,198.17f,142.53f},{-49.03f,199.61f,143.03f},{-48.8f,202.5f,143.58f},
     {-49.88f,205.99f,144.31f},{-53.7f,207.11f,144.94f},{-60.95f,210.74f,145.29f},{-66.7f,214.2f,145.82f}};
 auto at=[&](float u,float v){
  float s=u*(c.size()-1);int i=std::min(int(s),int(c.size()-2));
  V point=Sheet::cubic(c[std::max(0,i-1)],c[i],c[i+1],c[std::min(int(c.size()-1),i+2)],s-i);
  float high=mix(.71f,1.46f,step(.02f,.23f,u)*(1-step(.79f,.98f,u)));
  return point+V{.085f*(v-.5f),-.13f*std::sin(PI*v),(v-.5f)*2*high};
 };
 patch(86,6,at,tape);
 for(float v:{.021f,.975f}){
  std::vector<V> line;for(int j=0;j<=100;j++)line.push_back(at(j/100.f,v));tube(line,.113f,boundEdge,6,1);
 }
 V wall{-66.7f,218.15f,145.43f};
 lathe(wall,{0,-1,0},{{0,1.47f,fitting},{.38f,1.56f,fitting},{.59f,1.35f,fitting}},18);
 tube({wall+V{0,-.47f,0},wall+V{0,-2.17f,-.45f},wall+V{0,-4.02f,-.26f},wall+V{0,-4.55f,.89f}},.30f,fitting,8,4);
}
void sew(const Sheet& cloth,int heading,int seam,int thread){
 auto outer=[&](float u,float v,float gap){return cloth.point(u,v)+cloth.front(u,v)*gap;};
 // A real turned heading and a heavier double hem. All seams follow the
 // cloth coordinates and bend around the gathered waist and free ends.
 patch(112,7,[&](float u,float t){return outer(u,t*.047f,.085f);},heading);
 patch(112,7,[&](float u,float t){return outer(u,.959f+.041f*t,.115f);},heading);
 for(float v:{.047f,.959f,.997f}){
  std::vector<V> points;for(int j=0;j<=132;j++)points.push_back(outer(j/132.f,v,.145f));
  tube(points,v>.99f?.182f:.102f,seam,7,1);
 }
 for(float u:{.002f,.998f}){
  std::vector<V> points;for(int j=0;j<=113;j++)points.push_back(outer(u,j/113.f,.086f));
  tube(points,.13f,seam,7,1);
 }
 // Broken stitching along two hems merges to a modest line at the native scale.
 for(float v:{.042f,.9645f})for(int j=0;j<83;j++){
  float u=(j+.22f)/83.f,w=(j+.65f)/83.f;
  rod(outer(u,v,.155f),outer(w,v,.155f),.073f,thread,5);
 }
}
} // namespace dark_cloth

void blackoutDrape(){
 using namespace dark_cloth;
 const int cotton=mat({.098f,.173f,.196f},.98f,.001f,BlackoutCotton);
 const int rightCotton=mat({.089f,.149f,.167f},.98f,.001f,BlackoutCotton);
 const int turnback=mat({.144f,.188f,.194f},.98f,.001f,BlackoutCotton);
 const int seam=mat({.146f,.172f,.169f},.98f,.001f,BlackoutCotton);
 const int thread=mat({.220f,.231f,.210f},.98f,.001f,BlackoutCotton);
 const int binding=mat({.198f,.201f,.195f},.96f,.001f,BlackoutCotton);
 const int railMetal=mat({.264f,.272f,.261f},.45f,.145f,Brushed);
 const int wornMetal=mat({.397f,.379f,.315f},.41f,.21f,Brushed);
 const int liner=mat({.053f,.064f,.066f},.93f,.006f,Grain);
 box({-10.8f,216.9f,140.1f},{75.0f,1.25f,72.8f},liner,.24f);
 box({-10.8f,215.25f,102.93f},{76.3f,3.93f,1.59f},charcoal,.29f);
 rail(railMetal,wornMetal);
 for(bool left:{false,true}){
  Sheet cloth(left);
  patch(86,88,[&](float u,float v){return cloth.point(u,v);},left?cotton:rightCotton);
  sew(cloth,turnback,seam,thread);
  for(int i=0;i<4;i++)clip(cloth.anchors[i],i+(left?0:4),railMetal,wornMetal);
 }
 keeper(binding,thread,railMetal);
}
