#pragma once
void supplyGlassware(){
 // A single stoppered amber reagent bottle and a small fluted graduate.
 // Vary the silhouettes here; their paper labels have darkened with age.
 Scope shelf(translation({0,0,147}));
 int amberGlass=mat({.184f,.082f,.049f},.19f,.32f,Plain);
 int stopper=mat({.264f,.194f,.135f},.39f,.17f,Grain);
 int oldGum=mat({.445f,.383f,.266f},.90f,.003f,Paper);
 Scope bottlePlace(turn({-116.8f,203.1f,0},-20.f));
 lathe({},{0,0,1},{{0,4.3f,amberGlass},{.31f,4.99f,amberGlass},{1.04f,5.56f,amberGlass},
  {12.60f,5.59f,amberGlass},{14.2f,5.37f,amberGlass},{16.37f,4.67f,amberGlass},
  {18.43f,2.51f,amberGlass},{19.23f,2.03f,amberGlass},{22.38f,2.04f,amberGlass},
  {22.79f,2.48f,amberGlass},{23.62f,2.46f,amberGlass},{23.86f,2.08f,amberGlass}},40);
 lathe({0,0,23.63f},{0,0,1},{{0,1.52f,stopper},{.87f,1.64f,stopper},{1.25f,2.79f,stopper},
  {2.18f,2.97f,stopper},{3.19f,2.75f,stopper},{3.51f,2.25f,stopper}},22);
 patch(17,5,[&](float u,float v){
  float a=rad(-160+114*u),z=mix(11.06f,5.59f,v)+.33f*(u-.5f);
  float wear=(.24f*std::sin(u*23.4f+.8f)+.12f*std::sin(u*48.7f))*v*v;
  return V{5.623f*std::cos(a),5.623f*std::sin(a),z+wear};},oldGum);
}
void graduatedJug(){
 int oilGlass=mat({.099f,.125f,.12f},.24f,.43f,BlackGlass);
 int facet=mat({.139f,.172f,.157f},.27f,.28f,Plain);
 int lip=mat({.33f,.358f,.315f},.26f,.28f,Plain);
 Scope here(turn({-101.0f,204.5f,147},-18.f));
 auto shell=[](float u,float v,float inset){
  float a=2*PI*u,b=std::pow(std::max(0.f,std::cos(a+2.29f)),18.f)*std::pow(v,6.f);
  float r=mix(3.05f,5.03f,v)+.19f*std::cos(12*a)*(.4f+.6f*v)+1.81f*b-inset;
  return V{r*std::cos(a),r*std::sin(a),v*15.75f+.79f*b};
 };
 patch(60,6,[&](float u,float v){return shell(u,v,0);},oilGlass);
 patch(60,3,[&](float u,float v){return shell(u,.46f+.54f*v,.31f);},facet);
 std::vector<V> rim;for(int i=0;i<=72;i++)rim.push_back(shell(i/72.f,1,.14f));
 tube(rim,.195f,lip,7,1);
 lathe({},{0,0,1},{{0,3.12f,facet},{.42f,3.34f,facet},{.64f,3.11f,oilGlass}},28);
}
