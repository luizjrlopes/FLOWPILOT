import {getSession} from "./session";
const BASE=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export async function api<T=any>(path:string,init:RequestInit={}):Promise<T>{const s=getSession();const headers=new Headers(init.headers);headers.set("Content-Type","application/json");if(s)headers.set("Authorization",`Bearer ${s.token}`);const res=await fetch(BASE+path,{...init,headers,cache:"no-store"});if(!res.ok){let msg=`HTTP ${res.status}`;try{const j=await res.json();msg=j.detail||msg}catch{}throw new Error(msg)}return res.json()}
