import {createContext,useContext,useEffect,useMemo,useState} from "react";import {getMe} from "../api/authApi";
const Ctx=createContext(null);
export function AuthProvider({children}){const [user,setUser]=useState(()=>{try{return JSON.parse(sessionStorage.getItem("dq_user")||"null")}catch{return null}});const [booting,setBooting]=useState(true);
useEffect(()=>{const token=sessionStorage.getItem("dq_access_token");if(!token){setBooting(false);return;}getMe().then(raw=>{const u=normalizeUser(raw);setUser(u);sessionStorage.setItem("dq_user",JSON.stringify(u));}).catch(()=>{sessionStorage.removeItem("dq_access_token");sessionStorage.removeItem("dq_user");setUser(null);}).finally(()=>setBooting(false));},[]);
const saveAuth=data=>{sessionStorage.setItem("dq_access_token",data.accessToken);const u=normalizeUser(data.user);setUser(u);sessionStorage.setItem("dq_user",JSON.stringify(u));};
const logout=()=>{sessionStorage.removeItem("dq_access_token");sessionStorage.removeItem("dq_user");setUser(null);};
const value=useMemo(()=>({user,booting,saveAuth,logout,isAuthenticated:!!user}),[user,booting]);
return <Ctx.Provider value={value}>{children}</Ctx.Provider>}
export const useAuth=()=>useContext(Ctx);
export function normalizeUser(u={}){return {userId:u.userId||u.user_id||u.USER_ID,fullName:u.fullName||u.full_name||u.FULL_NAME||"User",email:u.email||u.EMAIL||"",role:String(u.role||u.USER_ROLE||"OPERATOR").toUpperCase()};}