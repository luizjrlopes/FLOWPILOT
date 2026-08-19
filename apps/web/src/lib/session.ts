import type {Session} from "./types";
const KEY="flowpilot-session";
export function getSession():Session|null{if(typeof window==='undefined')return null;const raw=localStorage.getItem(KEY);return raw?JSON.parse(raw):null}
export function setSession(s:Session){localStorage.setItem(KEY,JSON.stringify(s))}
export function clearSession(){localStorage.removeItem(KEY)}
