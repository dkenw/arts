#pragma once
#include <algorithm>
#include <array>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <string>
#include <thread>
#include <vector>

// Units throughout are centimetres. The camera, contact shadows, mirror rays
// and negative projected through the lens all use the same world space.
struct V{
 float x=0,y=0,z=0;
 V(){} V(float a,float b,float c):x(a),y(b),z(c){}
 float operator[](int i)const{return i==0?x:(i==1?y:z);}
 V operator+(V a)const{return {x+a.x,y+a.y,z+a.z};}
 V operator-(V a)const{return {x-a.x,y-a.y,z-a.z};}
 V operator-()const{return {-x,-y,-z};}
 V operator*(float a)const{return {x*a,y*a,z*a};}
 V operator/(float a)const{return *this*(1/a);}
 V operator*(V a)const{return{x*a.x,y*a.y,z*a.z};}
 V& operator+=(V a){x+=a.x;y+=a.y;z+=a.z;return *this;}
};
V operator*(float a,V b){return b*a;}
float dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
V cross(V a,V b){return {a.y*b.z-a.z*b.y,a.z*b.x-a.x*b.z,a.x*b.y-a.y*b.x};}
float len(V a){return std::sqrt(dot(a,a));}
V norm(V a){return a/(len(a)+1e-20f);}
float sat(float x){return std::clamp(x,0.f,1.f);}
float mix(float a,float b,float t){return a+(b-a)*t;}
V mix(V a,V b,float t){return a+(b-a)*t;}
float step(float a,float b,float x){float t=sat((x-a)/(b-a));return t*t*(3-2*t);}
float fract(float a){return a-std::floor(a);}
constexpr float PI=3.14159265359f;
float rad(float x){return x*PI/180;}
uint32_t hash32(uint32_t a){a^=a>>16;a*=0x7feb352du;a^=a>>15;a*=0x846ca68bu;return a^(a>>16);}
float hash(int x,int y,int z=0){return (hash32(uint32_t(x)*0x1f123bb5u^uint32_t(y)*0x5f356495u^uint32_t(z)*0x27d4eb2du)>>8)/16777216.f;}
struct RNG{uint32_t s;explicit RNG(uint32_t seed):s(seed){} float next(){s+=0x9e3779b9u;return (hash32(s)>>8)/16777216.f;}};
float noise(float x,float y,int seed=0){
 int ix=std::floor(x),iy=std::floor(y);float a=fract(x),b=fract(y);a=a*a*(3-2*a);b=b*b*(3-2*b);
 return mix(mix(hash(ix,iy,seed),hash(ix+1,iy,seed),a),mix(hash(ix,iy+1,seed),hash(ix+1,iy+1,seed),a),b);
}
struct Frame{
 V o{0,0,0},a{1,0,0},b{0,1,0},c{0,0,1};
 V dir(V p)const{return a*p.x+b*p.y+c*p.z;}
 V pos(V p)const{return o+dir(p);}
};
Frame frame;
Frame translation(V p){Frame f;f.o=p;return f;}
Frame turn(V p,float yaw,float pitch=0,float roll=0){
 float y=rad(yaw),x=rad(pitch),r=rad(roll);
 V a{std::cos(y),std::sin(y),0},b{-std::sin(y),std::cos(y),0},c{0,0,1};
 V bp=b*std::cos(x)+c*std::sin(x),cp=c*std::cos(x)-b*std::sin(x);
 return {p,a*std::cos(r)-cp*std::sin(r),bp,a*std::sin(r)+cp*std::cos(r)};
}
struct Scope{
 Frame old;
 explicit Scope(Frame q):old(frame){frame={old.pos(q.o),old.dir(q.a),old.dir(q.b),old.dir(q.c)};}
 ~Scope(){frame=old;}
};
struct UV{float u=0,v=0;};
struct Vertex{V p,n;UV tex;};
struct Tri{V p,e1,e2,na,nb,nc,lo,hi,mid;UV a,b,c;int mat;};
std::vector<Tri> tris;
V min3(V a,V b){return {std::min(a.x,b.x),std::min(a.y,b.y),std::min(a.z,b.z)};}
V max3(V a,V b){return {std::max(a.x,b.x),std::max(a.y,b.y),std::max(a.z,b.z)};}
void triangle(Vertex a,Vertex b,Vertex c,int m){
 V p=frame.pos(a.p),q=frame.pos(b.p),r=frame.pos(c.p),e=q-p,f=r-p;
 if(dot(cross(e,f),cross(e,f))<1e-12f)return;
 tris.push_back({p,e,f,frame.dir(a.n),frame.dir(b.n),frame.dir(c.n),min3(p,min3(q,r)),max3(p,max3(q,r)),(p+q+r)/3,a.tex,b.tex,c.tex,m});
}
void quad(V a,V b,V c,V d,int m){
 V n=norm(cross(b-a,c-a));Vertex A{a,n,{0,0}},B{b,n,{1,0}},C{c,n,{1,1}},D{d,n,{0,1}};
 triangle(A,B,C,m);triangle(A,C,D,m);
}
void face(V a,V b,V c,int m){
 V n=norm(cross(b-a,c-a));triangle({a,n,{}},{b,n,{1,0}},{c,n,{0,1}},m);
}
template<class F>void patch(int nu,int nv,F point,int mat){
 std::vector<Vertex> g;g.reserve((nu+1)*(nv+1));
 for(int y=0;y<=nv;y++)for(int x=0;x<=nu;x++){
  float u=float(x)/nu,v=float(y)/nv;
  V p=point(u,v);
  V a=point(std::min(1.f,u+.0006f),v)-point(std::max(0.f,u-.0006f),v);
  V b=point(u,std::min(1.f,v+.0006f))-point(u,std::max(0.f,v-.0006f));
  g.push_back({p,norm(cross(a,b)),{u,v}});
 }
 for(int j=0;j<nv;j++)for(int i=0;i<nu;i++){int k=j*(nu+1)+i,l=k+nu+1;
  triangle(g[k],g[k+1],g[l+1],mat);triangle(g[k],g[l+1],g[l],mat);}
}
void box(V center,V dims,int m,float bevel=0){
 V h=dims*.5f;float r=std::max(0.f,std::min({bevel,h.x*.90f,h.y*.90f,h.z*.90f}));
 for(int axis=0;axis<3;axis++)for(int side:{-1,1}){
  int ia=(axis+1)%3,ib=(axis+2)%3;float ha=h[ia],hb=h[ib];
  std::vector<float> a={-ha,ha},b={-hb,hb};
  if(r>0){a={-ha,-ha+r*.43f,-ha+r,ha-r,ha-r*.43f,ha};b={-hb,-hb+r*.43f,-hb+r,hb-r,hb-r*.43f,hb};}
  auto vert=[&](float u,float v){
   std::array<float,3>t{};t[axis]=side*h[axis];t[ia]=u;t[ib]=v;
   V p{t[0],t[1],t[2]},n;
   if(r>0){V q{std::clamp(p.x,-h.x+r,h.x-r),std::clamp(p.y,-h.y+r,h.y-r),std::clamp(p.z,-h.z+r,h.z-r)};n=norm(p-q);p=q+r*n;}
   else {t={0,0,0};t[axis]=side;n={t[0],t[1],t[2]};}
   return Vertex{p+center,n,{(u/ha+1)*.5f,(v/hb+1)*.5f}};
  };
  for(int j=0;j<int(b.size())-1;j++)for(int i=0;i<int(a.size())-1;i++){
   Vertex A=vert(a[i],b[j]),B=vert(a[i+1],b[j]),C=vert(a[i+1],b[j+1]),D=vert(a[i],b[j+1]);
   triangle(A,B,C,m);triangle(A,C,D,m);
  }
 }
}
struct Ring{float z,r;int mat;};
void lathe(V p,V axis,const std::vector<Ring>& profile,int sides=32,float phase=0){
 V z=norm(axis),a=norm(cross(std::abs(z.z)>.93f?V{0,1,0}:V{0,0,1},z)),b=cross(z,a);
 for(size_t i=1;i<profile.size();i++){auto q=profile[i-1],s=profile[i];float dz=s.z-q.z,dr=s.r-q.r;
  auto v=[&](const Ring& ring,int j,float vv){float t=phase+2*PI*j/sides;V r=a*std::cos(t)+b*std::sin(t);return Vertex{p+z*ring.z+r*ring.r,norm(r*dz-z*dr),{float(j)/sides,vv}};};
  for(int j=0;j<sides;j++){auto A=v(q,j,0),B=v(q,j+1,0),C=v(s,j+1,1),D=v(s,j,1);triangle(A,B,C,s.mat);triangle(A,C,D,s.mat);}
 }
 for(int end:{0,1}){auto q=end?profile.back():profile.front();if(q.r<.001)continue;
  V o=p+z*q.z,n=z*(end?1:-1);
  for(int j=0;j<sides;j++){float t=phase+2*PI*j/sides,u=t+2*PI/sides;
   triangle({o,n,{.5,.5}},{o+q.r*(a*std::cos(t)+b*std::sin(t)),n,{.5f+.5f*std::cos(t),.5f+.5f*std::sin(t)}},
   {o+q.r*(a*std::cos(u)+b*std::sin(u)),n,{.5f+.5f*std::cos(u),.5f+.5f*std::sin(u)}},q.mat);}
 }
}
void rod(V a,V b,float r,int m,int sides=16){lathe(a,b-a,{{0,r,m},{len(b-a),r,m}},sides);}
void tube(const std::vector<V>& knots,float radius,int m,int sides=9,int detail=3){
 std::vector<V> p;
 for(int i=0;i+1<int(knots.size());i++){
  V A=knots[std::max(0,i-1)],B=knots[i],C=knots[i+1],D=knots[std::min(int(knots.size())-1,i+2)];
  for(int j=0;j<detail;j++){float t=float(j)/detail,t2=t*t,t3=t2*t;
   p.push_back((B*2+(C-A)*t+(A*2-B*5+C*4-D)*t2+(-A+B*3-C*3+D)*t3)*.5f);}
 }p.push_back(knots.back());
 std::vector<Vertex> prev;V a{1,0,0};
 for(int i=0;i<int(p.size());i++){V t=norm(p[std::min(int(p.size())-1,i+1)]-p[std::max(0,i-1)]);
  if(std::abs(dot(t,a))>.997)a=std::abs(t.z)<.7f?V{0,0,1}:V{0,1,0};
  a=norm(a-t*dot(t,a));V b=cross(t,a);std::vector<Vertex> row;
  for(int j=0;j<=sides;j++){float angle=2*PI*j/sides;V n=a*std::cos(angle)+b*std::sin(angle);
   row.push_back({p[i]+n*radius,n,{float(j)/sides,float(i)/(p.size()-1)}});}
  if(i)for(int j=0;j<sides;j++){triangle(prev[j],prev[j+1],row[j+1],m);triangle(prev[j],row[j+1],row[j],m);}
  prev.swap(row);
 }
}
void torus(V c,V axis,float R,float r,int m,int steps=36){
 V t=norm(axis),a=norm(cross(std::abs(t.z)>.9f?V{0,1,0}:V{0,0,1},t)),b=cross(t,a);
 std::vector<V> p;for(int i=0;i<=steps;i++){float u=2*PI*i/steps;p.push_back(c+R*(a*std::cos(u)+b*std::sin(u)));}
 tube(p,r,m,8,1);
}
void oval(V c,V radii,int m,int w=24,int h=12){
 patch(w,h,[&](float u,float v){float a=2*PI*u,b=PI*(v-.5f);return c+V{radii.x*std::cos(a)*std::cos(b),radii.y*std::sin(a)*std::cos(b),radii.z*std::sin(b)};},m);
}
struct Ray{V o,d,inv;Ray(V p,V v):o(p),d(v),inv{1/(v.x+1e-20f),1/(v.y+1e-20f),1/(v.z+1e-20f)}{}};
struct Hit{float t=1e20f,u=0,v=0;int id=-1;};
struct Node{V lo,hi;int a=0,b=0,start=0,count=0;};
std::vector<Node> tree;std::vector<int> order;
int splitNode(int lo,int hi){
 Node n;n.lo={1e15f,1e15f,1e15f};n.hi=-n.lo;V ml=n.lo,mh=n.hi;
 for(int i=lo;i<hi;i++){const Tri&t=tris[order[i]];n.lo=min3(n.lo,t.lo);n.hi=max3(n.hi,t.hi);ml=min3(ml,t.mid);mh=max3(mh,t.mid);}
 int root=tree.size();tree.push_back(n);
 if(hi-lo<=6){tree[root].start=lo;tree[root].count=hi-lo;return root;}
 V d=mh-ml;int axis=d.y>d.x?1:0;if(d.z>d[axis])axis=2;
 int mid=(lo+hi)/2;std::nth_element(order.begin()+lo,order.begin()+mid,order.begin()+hi,[&](int a,int b){return tris[a].mid[axis]<tris[b].mid[axis];});
 int a=splitNode(lo,mid),b=splitNode(mid,hi);tree[root].a=a;tree[root].b=b;return root;
}
void buildTree(){order.resize(tris.size());for(int i=0;i<int(order.size());i++)order[i]=i;tree.reserve(tris.size()/2);splitNode(0,order.size());}
float bounds(const Ray& r,const Node& n,float far){
 V a=(n.lo-r.o)*r.inv,b=(n.hi-r.o)*r.inv,l=min3(a,b),h=max3(a,b);
 float near=std::max({l.x,l.y,l.z,0.f});return std::min({h.x,h.y,h.z,far})+.001f>=near?near:1e30f;
}
bool trace(const Ray&r,Hit&hit,bool shadow=false){
 int stack[96],n=1;stack[0]=0;
 while(n){const Node&node=tree[stack[--n]];
  if(bounds(r,node,hit.t)>hit.t)continue;
  if(node.count){for(int k=node.start;k<node.start+node.count;k++){
    int id=order[k];const Tri&t=tris[id];V pv=cross(r.d,t.e2);float det=dot(t.e1,pv);
    if(std::abs(det)<1e-8f)continue;float inv=1/det;V tv=r.o-t.p;float u=dot(tv,pv)*inv;
    if(u<0||u>1)continue;V q=cross(tv,t.e1);float v=dot(r.d,q)*inv;if(v<0||u+v>1)continue;
    float dist=dot(t.e2,q)*inv;if(dist>.012f&&dist<hit.t){hit={dist,u,v,id};if(shadow)return true;}
  }}else{
   float a=bounds(r,tree[node.a],hit.t),b=bounds(r,tree[node.b],hit.t);
   if(a<b){if(b<hit.t)stack[n++]=node.b;if(a<hit.t)stack[n++]=node.a;}
   else{if(a<hit.t)stack[n++]=node.a;if(b<hit.t)stack[n++]=node.b;}
  }
 }
 return hit.id>=0;
}
struct Pic{int w=1,h=1;std::vector<unsigned char> pix{128};
 void load(const std::string& file){std::ifstream s(file,std::ios::binary);std::string h0;int maxv;s>>h0>>w>>h>>maxv;s.get();
 if(!s||h0!="P5"||maxv!=255){std::cerr<<"Missing texture "<<file<<"\n";std::exit(2);}pix.resize(w*h);s.read((char*)pix.data(),pix.size());}
 float get(float u,float v)const{float fx=sat(u)*(w-1),fy=sat(v)*(h-1);int x=fx,y=fy,xx=std::min(x+1,w-1),yy=std::min(y+1,h-1);
 return mix(mix(pix[y*w+x],pix[y*w+xx],fx-x),mix(pix[yy*w+x],pix[yy*w+xx],fx-x),fy-y)/255.f;}
};
