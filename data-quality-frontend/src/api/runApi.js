import api from "./client";

export const getScorecard = async (runId) => (await api.get(`/runs/${encodeURIComponent(runId)}/scorecard`)).data;
export const getRuleResults = async (runId) => (await api.get(`/runs/${encodeURIComponent(runId)}/rule-results`)).data;
export const getRunExceptions = async (runId) => (await api.get(`/runs/${encodeURIComponent(runId)}/exceptions`)).data;
export const checkPublication = async (runId) => (await api.get(`/runs/${encodeURIComponent(runId)}/publication-check`)).data;
