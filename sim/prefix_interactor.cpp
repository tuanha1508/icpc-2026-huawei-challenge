// Fast C++ replacement for tools/interactor.py (706 lines of Python).
// Same event model, same tie-breaking, same scoring -- but ~50-100x faster, so a
// full 504-test corpus sweep with proper cross-validation costs seconds instead
// of the 10-45 minutes that forced every earlier analysis onto small samples.
// Usage: fast_interactor <test.txt> <solver-binary>
#include <bits/stdc++.h>
#include <unistd.h>
#include <sys/wait.h>
using namespace std;

static string fmt(double x){ char b[64]; snprintf(b,sizeof b,"%.9f",x); return b; }

struct Curve {
    vector<pair<int,double>> p;
    void add(int x,double y){ p.push_back({x,y}); }
    void done(){ sort(p.begin(),p.end()); }
    double at(double x) const {
        if(p.empty()) return 0.0;
        if(x<=p.front().first) return p.front().second;
        if(x>=p.back().first)  return p.back().second;
        size_t i=1; while(i<p.size() && p[i].first<x) ++i;
        double x0=p[i-1].first,y0=p[i-1].second,x1=p[i].first,y1=p[i].second;
        if(x1==x0) return y0;
        return y0+(y1-y0)*(x-x0)/(x1-x0);
    }
};

enum {ARRIVED,PRE_RUN,PRE_UP,PROC_RDY,PROC_RUN,PROC_DOWN,POST_RDY,POST_RUN,
      DEC_RDY,DPRE_RUN,DEC_UP,DPROC_RDY,DPROC_RUN,DEC_DOWN,DPOST_RDY,DPOST_RUN,DONE_};

struct Req {
    int rid=0,lin=0,lout=0,stage=ARRIVED,remote=-1,next_ls=0,iters=0;
    double arrival=0,tdr_done=0,firstTok=-1,lastTok=-1;
};

struct Ev {
    double t; int ord; long long seq; int kind;      // 0 ARR,1 TDN,2 XDN
    int rid=0;                                        // ARR
    string spec; double dur=0;                        // TDN
    function<vector<string>(double)> eff;
    bool up=false; int remote=0; long long size=0; string xk; vector<int> rids; // XDN
};
struct Cmp { bool operator()(const Ev&a,const Ev&b)const{
    if(a.t!=b.t) return a.t>b.t;
    if(a.ord!=b.ord) return a.ord>b.ord;
    return a.seq>b.seq; } };

struct Sim {
    int K=1,layers=1,N=0; double S=0,lat=0,bw=0; long long bpt=0;
    double SLO1=0,SLO2=0,tp_UB=0,tp_base=0,dist_base=0,w_tp=0,w_c=0;
    Curve col[6]; vector<vector<double>> rows;
    vector<Req> reqs;
    priority_queue<Ev,vector<Ev>,Cmp> heap; long long seq=0;
    bool busyE=false; vector<char> busyC; double up_free=0,down_free=0;
    double perTok=0;
    double transfer(double len) const { return lat + perTok*len; }
    void push(double t,int ord,int kind,Ev e){ e.t=t; e.ord=ord; e.seq=++seq; e.kind=kind; heap.push(e); }
    void startTask(double t,int sv,double dur,const string&spec,
                   function<vector<string>(double)> eff){
        if(sv<0) busyE=true; else busyC[sv]=1;
        Ev e; e.spec=spec; e.dur=dur; e.eff=eff;
        push(t+S+dur,0,1,e);
    }
    void enqueueTransfer(double t,bool up,int remote,long long ln,const string&kind,vector<int> rids){
        double tt=transfer((double)ln), start, doneT;
        if(up){ start=max(t,up_free); doneT=start+tt; up_free=doneT; }
        else  { start=max(t,down_free); doneT=start+tt; down_free=doneT; }
        Ev e; e.up=up; e.remote=remote; e.size=ln*bpt; e.xk=kind; e.rids=rids;
        push(doneT,1,2,e);
    }
    void applyXdn(bool up,const string&kind,const vector<int>&rids){
        for(int rid:rids){ Req&r=reqs[rid];
            if(kind=="PRE") r.stage = up?PROC_RDY:POST_RDY;
            else            r.stage = up?DPROC_RDY:DPOST_RDY; }
    }
};

int main(int argc,char**argv){
    if(argc<3){ fprintf(stderr,"usage: %s test solver\n",argv[0]); return 2; }
    ifstream in(argv[1]); if(!in){ fprintf(stderr,"cannot open test\n"); return 2; }
    Sim s;
    in>>s.K>>s.S>>s.lat>>s.bw>>s.bpt>>s.layers;
    in>>s.SLO1>>s.SLO2>>s.tp_UB>>s.tp_base>>s.dist_base>>s.w_tp>>s.w_c;
    in>>s.N;
    s.rows.resize(s.N);
    for(int i=0;i<s.N;++i){ s.rows[i].resize(7);
        for(int j=0;j<7;++j) in>>s.rows[i][j];
        for(int c=0;c<6;++c) if(s.rows[i][c+1]>=0.0) s.col[c].add((int)s.rows[i][0],s.rows[i][c+1]); }
    for(int c=0;c<6;++c) s.col[c].done();
    int R; in>>R; s.reqs.resize(R);
    for(int i=0;i<R;++i){ Req&r=s.reqs[i]; r.rid=i; in>>r.arrival>>r.lin>>r.lout; }
    s.busyC.assign(s.K,0);
    s.perTok = 8.0*(double)s.bpt/(s.bw*1e6);

    int toC[2],toP[2];
    if(pipe(toC)||pipe(toP)) return 2;
    pid_t pid=fork();
    if(pid==0){ dup2(toC[0],0); dup2(toP[1],1);
        close(toC[0]);close(toC[1]);close(toP[0]);close(toP[1]);
        execl(argv[2],argv[2],(char*)nullptr); _exit(127); }
    close(toC[0]); close(toP[1]);
    FILE*w=fdopen(toC[1],"w"); FILE*rd=fdopen(toP[0],"r");

    fprintf(w,"%d %s %s %s %lld %d\n",s.K,fmt(s.S).c_str(),fmt(s.lat).c_str(),
            fmt(s.bw).c_str(),s.bpt,s.layers);
    fprintf(w,"%s %s %s %s %s %s %s\n",fmt(s.SLO1).c_str(),fmt(s.SLO2).c_str(),
            fmt(s.tp_UB).c_str(),fmt(s.tp_base).c_str(),fmt(s.dist_base).c_str(),
            fmt(s.w_tp).c_str(),fmt(s.w_c).c_str());
    fprintf(w,"%d\n",s.N);
    for(auto&row:s.rows){ fprintf(w,"%d",(int)row[0]);
        for(int j=1;j<7;++j) fprintf(w," %s",fmt(row[j]).c_str()); fprintf(w,"\n"); }
    fflush(w);

    for(auto&r:s.reqs){ Ev e; e.rid=r.rid; s.push(r.arrival,2,0,e); }

    auto readTok=[&](string&out)->bool{ int c;
        do{ c=fgetc(rd); if(c==EOF) return false; }while(isspace(c));
        out.clear(); while(c!=EOF && !isspace(c)){ out.push_back((char)c); c=fgetc(rd); }
        return true; };

    long long frameNo=0, frameCap=LLONG_MAX;
    if(const char*e=getenv("PREFIX_FRAMES")) frameCap=atoll(e);
    while(!s.heap.empty()){
        if(++frameNo>frameCap) break;
        double t=s.heap.top().t;
        vector<Ev> batch;
        while(!s.heap.empty() && s.heap.top().t==t){ batch.push_back(s.heap.top()); s.heap.pop(); }
        vector<string> lines;
        for(auto&e:batch){
            if(e.kind==0){ Req&r=s.reqs[e.rid];
                lines.push_back("ARR "+to_string(r.rid)+" "+to_string(r.lin)); }
            else if(e.kind==1){
                lines.push_back("TDN "+e.spec+" "+fmt(e.dur));
                auto extra=e.eff(t); for(auto&x:extra) lines.push_back(x); }
            else { lines.push_back(string("XDN ")+(e.up?"UP ":"DOWN ")+to_string(e.remote)
                        +" "+to_string(e.size)+" "+e.xk+" "+to_string((int)e.rids.size())
                        +[&]{ string q; for(int i:e.rids) q+=" "+to_string(i); return q; }());
                   s.applyXdn(e.up,e.xk,e.rids); }
        }
        fprintf(w,"%s\n%d\n",fmt(t).c_str(),(int)lines.size());
        for(auto&l:lines) fprintf(w,"%s\n",l.c_str());
        fflush(w);

        string tok; if(!readTok(tok)) break;
        int n=atoi(tok.c_str());
        for(int i=0;i<n;++i){
            string sv; readTok(sv);
            int svidx = (sv=="E") ? -1 : atoi(sv.c_str()+1);
            string fam,step; readTok(fam); readTok(step);
            if(fam=="P"){
                if(step=="PRE"){ string a,b; readTok(a); readTok(b);
                    int remote=atoi(a.c_str()), rid=atoi(b.c_str());
                    Req&r=s.reqs[rid]; r.remote=remote; r.stage=PRE_RUN; r.next_ls=0;
                    double dur=s.col[0].at(r.lin); int rr=rid;
                    s.startTask(t,-1,dur,"E P PRE "+a+" "+b,[&s,rr](double tt){
                        Req&q=s.reqs[rr]; q.stage=PRE_UP; s.busyE=false;
                        s.enqueueTransfer(tt,true,q.remote,q.lin,"PRE",{q.rid});
                        return vector<string>{}; });
                } else if(step=="PROC"){ string a,b,c2,d; readTok(a);readTok(b);readTok(c2);readTok(d);
                    int ls=atoi(a.c_str()),le=atoi(b.c_str()),remote=atoi(c2.c_str()),rid=atoi(d.c_str());
                    Req&r=s.reqs[rid]; r.stage=PROC_RUN;
                    double dur=(double)(le-ls)/s.layers*s.col[1].at(r.lin); int rr=rid;
                    s.startTask(t,svidx,dur,"C"+to_string(remote)+" P PROC "+a+" "+b+" "+c2+" "+d,
                      [&s,rr,le](double tt){ Req&q=s.reqs[rr]; s.busyC[q.remote]=0; q.next_ls=le;
                        if(le==s.layers){ q.stage=PROC_DOWN;
                            s.enqueueTransfer(tt,false,q.remote,q.lin,"PRE",{q.rid}); }
                        else q.stage=PROC_RDY;
                        return vector<string>{}; });
                } else { string a,b; readTok(a); readTok(b);
                    int rid=atoi(b.c_str()); Req&r=s.reqs[rid]; r.stage=POST_RUN;
                    double dur=s.col[2].at(r.lin); int rr=rid;
                    s.startTask(t,-1,dur,"E P POST "+a+" "+b,[&s,rr](double tt){
                        Req&q=s.reqs[rr]; s.busyE=false; q.stage=DEC_RDY; q.tdr_done=tt;
                        return vector<string>{}; }); }
            } else {
                string mk; readTok(mk); int marker=atoi(mk.c_str());
                string ms; readTok(ms); int m=atoi(ms.c_str());
                vector<int> rids(m); string q;
                for(int j=0;j<m;++j){ string x; readTok(x); rids[j]=atoi(x.c_str()); q+=" "+x; }
                if(step=="PRE"){ for(int id:rids) s.reqs[id].stage=DPRE_RUN;
                    double dur=s.col[3].at(m);
                    s.startTask(t,-1,dur,"E D PRE -1 "+ms+q,[&s,rids](double tt){
                        s.busyE=false; map<int,vector<int>> byr;
                        for(int id:rids){ s.reqs[id].stage=DEC_UP; byr[s.reqs[id].remote].push_back(id); }
                        for(auto&kv:byr) s.enqueueTransfer(tt,true,kv.first,(long long)kv.second.size(),"DEC",kv.second);
                        return vector<string>{}; });
                } else if(step=="PROC"){ for(int id:rids) s.reqs[id].stage=DPROC_RUN;
                    double dur=s.col[4].at(m); int rem=marker;
                    s.startTask(t,svidx,dur,"C"+mk+" D PROC "+mk+" "+ms+q,[&s,rids,rem](double tt){
                        s.busyC[rem]=0; for(int id:rids) s.reqs[id].stage=DEC_DOWN;
                        s.enqueueTransfer(tt,false,rem,(long long)rids.size(),"DEC",rids);
                        return vector<string>{}; });
                } else { for(int id:rids) s.reqs[id].stage=DPOST_RUN;
                    double dur=s.col[5].at(m);
                    s.startTask(t,-1,dur,"E D POST -1 "+ms+q,[&s,rids](double tt){
                        s.busyE=false; vector<string> fins;
                        for(int id:rids){ Req&r=s.reqs[id]; r.iters++;
                            if(r.firstTok<0) r.firstTok=tt; r.lastTok=tt;
                            if(r.iters>=r.lout){ r.stage=DONE_; fins.push_back("FIN "+to_string(id)); }
                            else r.stage=DEC_RDY; }
                        return fins; }); }
            }
        }
    }
    fprintf(w,"END\n"); fflush(w); fclose(w); fclose(rd);
    int st; waitpid(pid,&st,0);

    long long totalTok=0; double firstArr=1e300,lastTok=-1e300,tdrSum=0;
    long long gaps=0; double span=0; long long nTdr=0;
    for(auto&r:s.reqs){ firstArr=min(firstArr,r.arrival);
        if(r.lastTok>-1e299){ lastTok=max(lastTok,r.lastTok); totalTok+=r.iters; }
        if(r.tdr_done>0){ tdrSum+=r.tdr_done-r.arrival; ++nTdr; }
        if(r.iters>1){ gaps+=r.iters-1; span+=r.lastTok-r.firstTok; } }
    if(nTdr==0) nTdr=1;
    double elapsed=lastTok-firstArr;
    double tp = elapsed>0 ? totalTok/elapsed : 1e300;
    double tdr = tdrSum/(double)nTdr;
    double tpot = gaps>0 ? span/(double)gaps : 0.0;
    double exT = max(0.0,(tdr-s.SLO1)/s.SLO1), exP = max(0.0,(tpot-s.SLO2)/s.SLO2);
    double dist = sqrt(exT*exT+exP*exP);
    double ctp;
    if(s.tp_UB==s.tp_base) ctp = (tp==s.tp_UB)?1.0:0.0;
    else ctp = max(0.0,min(1.0,(tp-s.tp_base)/(s.tp_UB-s.tp_base)));
    double cc = s.dist_base>0 ? max(0.0,1.0-dist/s.dist_base) : (dist==0?1.0:0.0);
    printf("frames=%lld score=%.3f tp=%.6f tdr=%.6f tpot=%.6f dist=%.4f elapsed=%.3f\n",
           frameNo, 1000.0*(s.w_tp*ctp+s.w_c*cc), tp, tdr, tpot, dist, elapsed);
    return 0;
}
