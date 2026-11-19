#include "scene/draw.cpp"
#include "scene/camera.hpp"
#include "scene/draft.hpp"
#include <stdexcept>

namespace {
std::vector<Tri> rest;
std::vector<int> affectedNodes;
std::vector<dark_cloth::Link> constraints,yarn,bias;
std::vector<uint8_t> sampleGrid(width*height,6);
draft::Response response;

// Give the tied panel a target under air pressure, then let its warp, weft
// and bias share the load. The original positions supply the edge lengths.
void fitCloth(dark_cloth::Sheet& sheet,std::array<float,2> q){
 using namespace dark_cloth;
 const auto& hanging=*restingSheet;
 const V direction=norm(V{.992f,-.12f,0});
 std::vector<V> target(hanging.p.size());
 std::vector<float> free(hanging.p.size());
 for(int row=0;row<=ny;row++)for(int col=0;col<=nx;col++){
  int k=index(col,row);V p=hanging.p[k];
  float u=float(col)/nx,drop=std::max(0.f,142.0f-p.z);
  float upper=sat((p.z-146.0f)/34.5f);
  float pocket=std::pow(std::max(0.f,std::sin(PI*upper)),1.45f);
  float drive=mix(q[0],q[1],step(.14f,.95f,u));
  float tilt=rad(10.9f)*drive*step(0.f,9.8f,drop);
  V swing=direction*(drop*std::sin(tilt))+V{0,0,drop*(1-std::cos(tilt))};
  V bow=V{4.6f+.55f*std::sin(2*PI*u),-3.0f-.75f*std::cos(2*PI*u),.52f}*(.84f*pocket*drive);
  free[k]=hanging.mobility[k]&&p.z<179.9f&&(p.z<141.8f||p.z>146.4f)?1.f:0.f;
  sheet.p[k]=target[k]=p+(swing+bow)*free[k];
 }
 auto relax=[&](const std::vector<Link>& edges,int pass,float weight){
  for(size_t j=0;j<edges.size();j++){
   const auto& e=edges[(pass&1)?edges.size()-1-j:j];
   float a=free[e.a],b=free[e.b];
   if(a+b==0)continue;
   V edge=sheet.p[e.b]-sheet.p[e.a];float d=len(edge);
   if(d<.0001f)continue;
   V correction=edge*((d-e.length)*(e.strength*weight)/((a+b)*d));
   sheet.p[e.a]+=correction*a;sheet.p[e.b]+=correction*(-b);
  }
 };
 for(int pass=0;pass<85;pass++){
  if(pass<66)for(size_t k=0;k<sheet.p.size();k++)sheet.p[k]+=(target[k]-sheet.p[k])*(.038f*free[k]);
  relax(constraints,pass,1);
 }
 // Preserve individual warp and weft lengths first. A gathered sheet can
 // shear on the bias and open a pleat without stretching the threads.
 for(int pass=0;pass<270;pass++){relax(bias,pass,.22f);relax(yarn,pass,1);}
 for(int pass=0;pass<180;pass++)relax(yarn,pass,1);
}
void rememberCloth(){
 using namespace dark_cloth;
 rest.assign(tris.begin()+leftBegin,tris.begin()+leftEnd);
 constraints=restingSheet->links;
 for(auto& e:constraints){
  e.length=len(restingSheet->p[e.b]-restingSheet->p[e.a]);
  int dx=std::abs(e.a%(nx+1)-e.b%(nx+1)),dy=std::abs(e.a/(nx+1)-e.b/(nx+1));
  if(dx+dy==1)yarn.push_back(e);
  else if(dx==1&&dy==1)bias.push_back(e);
 }
 std::vector<bool> changed(tris.size()),dirty(tree.size());
 std::fill(changed.begin()+leftBegin,changed.begin()+leftEnd,true);
 for(int i=int(tree.size())-1;i>=0;i--){
  auto& node=tree[i];
  if(node.count){
   for(int j=node.start;j<node.start+node.count;j++)if(changed[order[j]])dirty[i]=true;
  }else dirty[i]=dirty[node.a]||dirty[node.b];
  if(dirty[i])affectedNodes.push_back(i);
 }
}

void setPose(std::array<float,2> q){
 bool neutral=q[0]==0&&q[1]==0;
 // Barycentric rest coordinates keep the worn fibres attached to their folds.
 dark_cloth::restMesh=neutral?nullptr:rest.data();
 if(neutral){
  std::copy(rest.begin(),rest.end(),tris.begin()+dark_cloth::leftBegin);
 }else{
  auto sheet=*dark_cloth::restingSheet;fitCloth(sheet,q);
  size_t originalSize=tris.size();
  dark_cloth::drawPanel(sheet,dark_cloth::panelMaterials);
  if(tris.size()-originalSize!=rest.size())throw std::runtime_error("The sewn panel changed tessellation.");
  std::copy(tris.begin()+originalSize,tris.end(),tris.begin()+dark_cloth::leftBegin);
  tris.resize(originalSize);
 }
 for(int i:affectedNodes){
  Node& n=tree[i];
  if(n.count){
   n.lo=tris[order[n.start]].lo;n.hi=tris[order[n.start]].hi;
   for(int j=n.start+1;j<n.start+n.count;j++){
    const Tri& t=tris[order[j]];n.lo=min3(n.lo,t.lo);n.hi=max3(n.hi,t.hi);
   }
  }else{n.lo=min3(tree[n.a].lo,tree[n.b].lo);n.hi=max3(tree[n.a].hi,tree[n.b].hi);}
 }
}

struct Sample{V rgb;float depth=0,cotton=0;unsigned char mat=0;};
std::vector<Sample> photograph(const std::vector<uint32_t>& pixels,int maxSide,int threads){
 std::atomic<int> next{0};std::vector<Sample> result(pixels.size());
 auto worker=[&](){

  for(;;){
   int from=next.fetch_add(10);
   if(from>=int(pixels.size()))return;
   for(int k=from;k<std::min(from+10,int(pixels.size()));k++){
    int pixel=pixels[k],x=pixel%width,y=pixel/width;
    int side=std::min(maxSide,int(sampleGrid[pixel])),count=side*side;
    cameraSampleCount=count;
    std::array<int,256> votes{};Sample s;
    uint32_t seed=hash32(pixel+401);
    for(int j=0;j<count;j++){
     cameraSample=j;RNG rng(hash32(seed+0x9e3779b9u*(1+j)));
     float ax=(j%side+.16f+.68f*rng.next())/side,ay=(j/side+.16f+.68f*rng.next())/side;
     V dir=norm(forward+right*((x+ax-width*.5f)/focalLength)+up*((height*.5f-y-ay)/focalLength));
     float angle=2*PI*rng.next(),radius=lensOpening*std::sqrt(rng.next());
     V lens=eye+right*(radius*std::cos(angle))+up*(radius*std::sin(angle));
     V focus=eye+dir*(focusDistance/dot(dir,forward));
     auto hit=renderRay(Ray(lens,norm(focus-lens)),rng,0,count);
     int mat=std::max(hit.mat,0);
     s.rgb+=hit.color;s.depth+=hit.depth;votes[mat]++;
     s.cotton+=mats[mat].kind==BlackoutCotton;
    }
    s.rgb=s.rgb/count;s.depth/=count;s.cotton/=count;
    s.mat=std::max_element(votes.begin(),votes.end())-votes.begin();
    result[k]=s;
   }
  }
 };
 std::vector<std::thread> pool;for(int t=1;t<threads;t++)pool.emplace_back(worker);
 worker();for(auto& t:pool)t.join();return result;
}

std::vector<uint32_t> sweptPixels(int threads){
 // This window covers the free edge and its projected shadows from both the
 // finite safelight and the paper return. Two poses find the changing receivers.
 constexpr int x0=133,x1=365,y0=36,y1=192;
 std::vector<uint32_t> window;
 for(int y=y0;y<=y1;y++)for(int x=x0;x<=x1;x++)window.push_back(y*width+x);
 auto still=photograph(window,3,threads);
 std::vector<bool> swept(width*height);
 for(auto pose:{response.at(1.23f),response.at(2.32f),response.at(4.97f)}){
  setPose(pose);auto now=photograph(window,3,threads);
  for(size_t j=0;j<window.size();j++){
   V d=now[j].rgb-still[j].rgb;
   if(std::max({std::abs(d.x),std::abs(d.y),std::abs(d.z)})<.00026f &&
      std::abs(now[j].depth-still[j].depth)<.045f && still[j].mat==now[j].mat)continue;
   int x=window[j]%width,y=window[j]/width;
   float difference=std::max({std::abs(d.x),std::abs(d.y),std::abs(d.z)});
   uint8_t grid=still[j].cotton>0||now[j].cotton>0||difference>.047f?12:(difference>.0055f?9:6);
   for(int yy=y-2;yy<=y+2;yy++)for(int xx=x-2;xx<=x+2;xx++){
    int id=yy*width+xx;swept[id]=true;sampleGrid[id]=std::max(sampleGrid[id],grid);
   }
  }
 }
 setPose({});std::vector<uint32_t> pixels;
 for(int i=0;i<width*height;i++)if(swept[i])pixels.push_back(i);
 return pixels;
}

std::vector<int> keyFrames(){
 std::vector<int> keys{0};
 auto last=response.at(0);
 for(int f=1;f<loopFrames;f++){
  auto q=response.at(f/framesPerSecond);
  float delta=std::max(std::abs(q[0]-last[0]),std::abs(q[1]-last[1]));
  // Resolve a moving edge in small fractions of a native pixel. Sample the
  // tips of each reversal even where the displacement changes slowly.
  bool moving=std::abs(q[0])+std::abs(q[1])>.005f;
  if(delta>.051f||(moving&&f-keys.back()>=6)){
   keys.push_back(f);last=q;
  }else if(!moving&&std::abs(last[0])+std::abs(last[1])>.005f){
   keys.push_back(f);last=q;
  }
 }
 if(keys.back()<338)keys.push_back(338);
 keys.push_back(loopFrames);return keys;
}

template<class T> void write(std::ofstream& out,const T& value){
 out.write(reinterpret_cast<const char*>(&value),sizeof(value));
}
} // namespace

int main(int argc,char**argv){
 if(argc!=4){std::cerr<<"cloth WORK SAMPLE_GRID_SIDE THREADS\n";return 2;}
 std::string work=argv[1];
 int side=std::max(2,std::stoi(argv[2])),threads=std::max(1,std::stoi(argv[3]));
 for(int i=0;i<int(plates.size());i++)plates[i].load(work+"/plate"+std::to_string(i)+".pgm");
 dark_cloth::capturePoseMesh=true;
 rinse::setTime(0);materials();makeRoom();details();woolScarf();setLights();
 rinse::movingGeometry();buildTree();waterLight.bake();basinLight.prepare();basinLight.bake();
 useStillSampler=true;rememberCloth();auto pixels=sweptPixels(threads);
 auto keys=keyFrames();
 std::cerr<<keys.size()<<" resolved folds and rests.\n";
 auto original=photograph(pixels,side,threads);
 std::ofstream out(work+"/cloth.bin",std::ios::binary);out.write("CLOTH_01",8);
 for(uint32_t n:{uint32_t(width),uint32_t(height),uint32_t(loopFrames),uint32_t(pixels.size()),uint32_t(keys.size())})write(out,n);
 for(uint32_t pix:pixels)write(out,pix);
 for(const auto& s:original)write(out,s.cotton);
 for(int frame:keys){
  auto q=response.at(frame/framesPerSecond);setPose(q);
  bool resting=q[0]==0&&q[1]==0;
  auto now=resting?original:photograph(pixels,side,threads);
  write(out,uint32_t(frame));
  for(size_t j=0;j<now.size();j++){
   write(out,now[j].rgb-original[j].rgb);write(out,now[j].depth-original[j].depth);
   write(out,now[j].cotton);write(out,now[j].mat);
  }
  std::cerr<<"Cloth pose "<<frame<<"/"<<loopFrames<<" on "<<pixels.size()<<" pixels\n";
 }
 return out?0:2;
}
