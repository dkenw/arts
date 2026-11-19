#include "scene/draw.cpp"
#include <chrono>
#include <iomanip>
#include <sstream>

#include "scene/camera.hpp"
struct Pixel {int x,y;};
size_t staticTris,staticTree;
std::string root;
std::vector<Pixel> area;
void addWaterAt(float t){
 rinse::setTime(t);tris.resize(staticTris);tree.resize(staticTree);order.resize(staticTris);
 rinse::movingGeometry();
 for(size_t i=staticTris;i<tris.size();i++)order.push_back(i);
 int dynamicRoot=splitNode(staticTris,order.size()),fixedRoot=staticTree-1;
 Node combined;combined.a=fixedRoot;combined.b=dynamicRoot;
 combined.lo=min3(tree[fixedRoot].lo,tree[dynamicRoot].lo);
 combined.hi=max3(tree[fixedRoot].hi,tree[dynamicRoot].hi);tree[0]=combined;
 basinLight.bake();
}
void expose(int samples,int threads,int shutter,
            std::vector<V>& sum,std::vector<float>& distance,
            std::vector<std::array<unsigned char,256>>& votes,std::vector<float>& fiber){

 std::atomic<int> work{0};
 auto run=[&](){
  for(;;){
   int start=work.fetch_add(32);if(start>=int(area.size()))break;
   for(int index=start;index<std::min(int(area.size()),start+32);index++){
    auto [x,y]=area[index];int pix=y*width+x;
    int local=samples;
    if(x>=102&&x<=113&&y>=164&&y<=263)local=std::max(samples,64);
    int side=std::round(std::sqrt(float(local)));V col{};float depth=0,exposedFiber=0;
    cameraSampleCount=local;
    uint32_t seed=hash32(pix+401);
    for(int j=0;j<local;j++){
     if(((j%side+j/side)&1)!=shutter)continue;
     cameraSample=j;
     RNG rng(hash32(seed+0x9e3779b9u*(1+j)));
     float ax=(j%side+.14f+.72f*rng.next())/side,ay=(j/side+.14f+.72f*rng.next())/side;
     V dir=norm(forward+right*((x+ax-width*.5f)/focalLength)+up*((height*.5f-y-ay)/focalLength));
     float angle=2*PI*rng.next(),radius=lensOpening*std::sqrt(rng.next());
     V lens=eye+right*(radius*std::cos(angle))+up*(radius*std::sin(angle));
     V focus=eye+dir*(focusDistance/dot(dir,forward));
     Ray camera(lens,norm(focus-lens));
     auto sample=renderRay(camera,rng,0,local);
     if(sample.mat==sheets[3]){
      // The very thin water film still colours stock as it breaks the surface.
      // The curled tip can rise far enough to show the full paper response.
      V p=camera.o+camera.d*sample.depth;
      float clearance=p.z-rinse::height(p.x,p.y);
      exposedFiber+=.22f+.78f*step(.008f,.24f,clearance);
     }
     col+=sample.color;depth+=sample.depth;
     votes[index][std::max(0,sample.mat)]++;
    }
    sum[index]+=col/local;distance[index]+=depth/local;fiber[index]+=exposedFiber/local;
   }
  }
 };
 std::vector<std::thread> pool;
 for(int i=1;i<threads;i++)pool.emplace_back(run);
 run();for(auto &worker:pool)worker.join();
}
void renderWet(int picture,int samples,int threads){
 std::vector<V> colors(area.size());std::vector<float> depths(area.size());
 std::vector<unsigned char> ids(area.size());
 std::vector<std::array<unsigned char,256>> votes(area.size());
 std::vector<float> fiber(area.size());
 for(int shutter=0;shutter<2;shutter++){
  float t=(picture%waterFrames)/framesPerSecond+(shutter? .0061f:-.0061f);
  if(t<0)t+=rinse::period;
  addWaterAt(t);expose(samples,threads,shutter,colors,depths,votes,fiber);
 }
 for(size_t i=0;i<ids.size();i++)
  ids[i]=std::max_element(votes[i].begin(),votes[i].end())-votes[i].begin();
 std::ostringstream name;name<<root<<"/flow-"<<std::setfill('0')<<std::setw(3)<<picture;
 std::vector<unsigned char> coverage(area.size());
 for(size_t i=0;i<coverage.size();i++)coverage[i]=std::lround(255*sat(fiber[i]));
 std::ofstream film(name.str()+".film",std::ios::binary);
 film.write(reinterpret_cast<const char*>(coverage.data()),coverage.size());
 if(!film)throw std::runtime_error("Could not write wet-stock coverage.");
 std::ofstream f(name.str()+".wet",std::ios::binary);
 f.write(reinterpret_cast<const char*>(colors.data()),colors.size()*sizeof(V));
 f.write(reinterpret_cast<const char*>(depths.data()),depths.size()*sizeof(float));
 f.write(reinterpret_cast<const char*>(ids.data()),ids.size());
 if(!f)throw std::runtime_error("Could not write wet pass.");
}
int main(int argc,char**argv){
 if(argc<7){std::cerr<<"flow WORK SAMPLE_COUNT THREADS FIRST LAST STEP\n";return 2;}
 root=argv[1];int samples=std::stoi(argv[2]),threads=std::stoi(argv[3]);
 int first=std::stoi(argv[4]),last=std::stoi(argv[5]),stride=std::stoi(argv[6]);
 for(int i=0;i<int(plates.size());i++)plates[i].load(root+"/plate"+std::to_string(i)+".pgm");
 std::ifstream mask(root+"/active.u8",std::ios::binary);if(!mask)return 2;
 for(int y=0;y<height;y++)for(int x=0;x<width;x++){char active=0;mask.get(active);if(active)area.push_back({x,y});}
 if(!mask||area.empty())return 2;
 rinse::setTime(0);materials();makeRoom();details();woolScarf();setLights();buildTree();
 waterLight.bake();basinLight.prepare();
 staticTris=tris.size();tree.push_back(tree.front());staticTree=tree.size();
 std::cerr<<area.size()<<" wet-area pixels, "<<staticTris<<" stationary triangles\n";
 for(int frame=first;frame<=last;frame+=stride){
  auto tic=std::chrono::steady_clock::now();
  renderWet(frame,samples,threads);
  auto done=std::chrono::steady_clock::now();
  std::cerr<<"frame "<<frame<<", "<<std::chrono::duration<double>(done-tic).count()<<" s\n";
 }
}
