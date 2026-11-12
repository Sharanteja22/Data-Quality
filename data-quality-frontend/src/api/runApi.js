import api from "./client";
export const getScorecard=async id=>(await api.get(`/runs/${encodeURIComponent(id)}/scorecard`)).data;
export const getRuleResults=async id=>(await api.get(`/runs/${encodeURIComponent(id)}/rule-results`)).data;
export const getRunExceptions=async id=>(await api.get(`/runs/${encodeURIComponent(id)}/exceptions`)).data;
export const checkPublication=async id=>(await api.get(`/runs/${encodeURIComponent(id)}/publication-check`)).data;