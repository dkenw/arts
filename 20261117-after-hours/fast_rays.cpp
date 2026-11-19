// Exact primitive intersections with a bounding-volume hierarchy.
// This accelerates the existing scene; it does not change the drawing model.
#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <numeric>
#include <vector>

struct V { double x,y,z; double operator[](int i) const {return i==0?x:i==1?y:z;} double &operator[](int i){return i==0?x:i==1?y:z;} };
V operator+(V a,V b){return {a.x+b.x,a.y+b.y,a.z+b.z};}
V operator-(V a,V b){return {a.x-b.x,a.y-b.y,a.z-b.z};}
V operator*(V a,double t){return {a.x*t,a.y*t,a.z*t};}
double dot(V a,V b){return a.x*b.x+a.y*b.y+a.z*b.z;}
V unit(V a){return a*(1/std::max(std::sqrt(dot(a,a)),1e-15));}
V readv(const double *a){return {a[0],a[1],a[2]};}
constexpr double INF=std::numeric_limits<double>::infinity();
constexpr double EPS=1e-5;
struct Shape {int kind; V p,a,b,n,lo,hi; double len; std::array<double,9> rot;};
struct Node {V lo,hi;int left=-1,right=-1,start=0,count=0;};
std::vector<Shape> shapes;
std::vector<Node> nodes;
std::vector<int> order;
V minimum(V a,V b){return {std::min(a.x,b.x),std::min(a.y,b.y),std::min(a.z,b.z)};}
V maximum(V a,V b){return {std::max(a.x,b.x),std::max(a.y,b.y),std::max(a.z,b.z)};}
V local(V v,const Shape &s){return {v.x*s.rot[0]+v.y*s.rot[3]+v.z*s.rot[6],v.x*s.rot[1]+v.y*s.rot[4]+v.z*s.rot[7],v.x*s.rot[2]+v.y*s.rot[5]+v.z*s.rot[8]};}
V world(V v,const Shape &s){return {v.x*s.rot[0]+v.y*s.rot[1]+v.z*s.rot[2],v.x*s.rot[3]+v.y*s.rot[4]+v.z*s.rot[5],v.x*s.rot[6]+v.y*s.rot[7]+v.z*s.rot[8]};}
int build(int start,int end){
 int id=nodes.size();nodes.emplace_back();V lo{INF,INF,INF},hi{-INF,-INF,-INF};
 for(int i=start;i<end;i++){lo=minimum(lo,shapes[order[i]].lo);hi=maximum(hi,shapes[order[i]].hi);}
 nodes[id].lo=lo;nodes[id].hi=hi;
 if(end-start<=5){nodes[id].start=start;nodes[id].count=end-start;return id;}
 V extent=hi-lo;int axis=extent.y>extent.x?1:0;if(extent.z>extent[axis])axis=2;
 int mid=(start+end)/2;
 std::nth_element(order.begin()+start,order.begin()+mid,order.begin()+end,[axis](int a,int b){return shapes[a].lo[axis]+shapes[a].hi[axis]<shapes[b].lo[axis]+shapes[b].hi[axis];});
 int left=build(start,mid),right=build(mid,end);nodes[id].left=left;nodes[id].right=right;return id;
}
extern "C" void load_scene(const double *data,int count){
 shapes.clear();nodes.clear();order.resize(count);std::iota(order.begin(),order.end(),0);shapes.reserve(count);nodes.reserve(count*2);
 for(int j=0;j<count;j++){
  const double *v=data+j*32;Shape s{};s.kind=(int)v[0];s.p=readv(v+1);s.a=readv(v+4);s.b=readv(v+7);s.n=readv(v+10);s.len=v[13];std::copy(v+14,v+23,s.rot.begin());
  if(s.kind==0){s.lo=s.p;s.hi=s.a;}
  else if(s.kind==1){s.lo=minimum(minimum(s.p,s.p+s.a),minimum(s.p+s.b,s.p+s.a+s.b));s.hi=maximum(maximum(s.p,s.p+s.a),maximum(s.p+s.b,s.p+s.a+s.b));}
  else if(s.kind==2){V radius{};for(int k=0;k<3;k++)for(int q=0;q<3;q++)radius[k]+=std::pow(s.rot[k*3+q]*s.a[q],2);for(int k=0;k<3;k++)radius[k]=std::sqrt(radius[k]);s.lo=s.p-radius;s.hi=s.p+radius;}
  else {V radius{s.b.x,s.b.x,s.b.x};s.lo=minimum(s.p,s.p+s.a*s.len)-radius;s.hi=maximum(s.p,s.p+s.a*s.len)+radius;}
  s.lo=s.lo-V{1e-8,1e-8,1e-8};s.hi=s.hi+V{1e-8,1e-8,1e-8};shapes.push_back(s);
 }
 if(count)build(0,count);
}
bool bounds(V ro,V rd,const Node &node,double best){
 double near=0,far=best;
 for(int k=0;k<3;k++){
  if(std::abs(rd[k])<1e-15){if(ro[k]<node.lo[k]||ro[k]>node.hi[k])return false;continue;}
  double a=(node.lo[k]-ro[k])/rd[k],b=(node.hi[k]-ro[k])/rd[k];if(a>b)std::swap(a,b);
  near=std::max(near,a);far=std::min(far,b);if(far<near)return false;
 }return true;
}
bool hit(V ro,V rd,const Shape &s,double &t,V &normal){
 t=INF;
 if(s.kind==0){
  double enter=-INF,leave=INF;
  for(int k=0;k<3;k++){
   if(std::abs(rd[k])<1e-15){if(ro[k]<s.p[k]||ro[k]>s.a[k])return false;continue;}
   double a=(s.p[k]-ro[k])/rd[k],b=(s.a[k]-ro[k])/rd[k];if(a>b)std::swap(a,b);enter=std::max(enter,a);leave=std::min(leave,b);
  }
  if(leave<enter)return false;t=enter>EPS?enter:leave;if(t<=EPS)return false;
  V p=ro+rd*t;double closest=INF;normal={0,0,0};int face=0;
  for(int k=0;k<6;k++){double d=std::abs(p[k%3]-(k<3?s.p[k]:s.a[k%3]));if(d<closest){closest=d;face=k;}}
  normal[face%3]=face<3?-1:1;return true;
 }
 if(s.kind==1){
  double den=dot(rd,s.n);if(std::abs(den)<1e-10)return false;t=dot(s.p-ro,s.n)/den;if(t<=EPS)return false;
  V p=ro+rd*t-s.p;double u=dot(p,s.a)/dot(s.a,s.a),v=dot(p,s.b)/dot(s.b,s.b);if(u<0||u>1||v<0||v>1)return false;
  normal=s.n*(den>0?-1:1);return true;
 }
 if(s.kind==2){
  V oc=local(ro-s.p,s),dr=local(rd,s);for(int k=0;k<3;k++){oc[k]/=s.a[k];dr[k]/=s.a[k];}
  double aa=dot(dr,dr),bb=dot(oc,dr),cc=dot(oc,oc)-1,disc=bb*bb-aa*cc;if(disc<0)return false;
  double root=std::sqrt(disc);t=(-bb-root)/aa;if(t<=EPS)t=(-bb+root)/aa;if(t<=EPS)return false;
  V p=local(ro+rd*t-s.p,s);for(int k=0;k<3;k++)p[k]/=s.a[k]*s.a[k];normal=unit(world(p,s));return true;
 }
 V oc=ro-s.p;double da=dot(rd,s.a),oa=dot(oc,s.a);V dp=rd-s.a*da,op=oc-s.a*oa;
 double aa=dot(dp,dp),bb=dot(dp,op),cc=dot(op,op)-s.b.x*s.b.x,disc=bb*bb-aa*cc,cap=0;
 if(disc>=0&&aa>1e-18){
  double root=std::sqrt(disc);for(double u:{(-bb-root)/aa,(-bb+root)/aa}){double h=oa+u*da;if(u>EPS&&u<t&&h>=0&&h<=s.len)t=u;}
 }
 if(std::abs(da)>1e-9){for(int i=0;i<2;i++){double h=i?s.len:0,tc=(h-oa)/da;V radial=op+dp*tc;if(tc>EPS&&tc<t&&dot(radial,radial)<=s.b.x*s.b.x){t=tc;cap=i?1:-1;}}}
 if(!std::isfinite(t))return false;V rel=ro+rd*t-s.p;normal=cap?s.a*cap:unit(rel-s.a*dot(rel,s.a));return true;
}
extern "C" void trace(const double *origins,const double *directions,int count,double *depth,int *ids,double *normals){
 #pragma omp parallel for schedule(static)
 for(int i=0;i<count;i++){
  V ro=readv(origins+i*3),rd=readv(directions+i*3),normal{};double best=INF;int found=-1,stack[128],top=0;if(!nodes.empty())stack[top++]=0;
  while(top){const Node &node=nodes[stack[--top]];if(!bounds(ro,rd,node,best))continue;
   if(node.count){for(int j=node.start;j<node.start+node.count;j++){int index=order[j];V n;double t;if(hit(ro,rd,shapes[index],t,n)&&(t<best||(t==best&&index<found))){best=t;found=index;normal=n;}}}
   else{stack[top++]=node.left;stack[top++]=node.right;}
  }
  depth[i]=best;ids[i]=found;for(int k=0;k<3;k++)normals[i*3+k]=normal[k];
 }
}
