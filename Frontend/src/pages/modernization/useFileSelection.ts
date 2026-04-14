import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import {
  listExampleXml,
  listExampleExcel,
  parseIpPlanFromExample,
} from '../../api/client';
import type { IpPreviewData } from '../../types';
import type { LogEntry } from '../../components/DebugConsole';

interface Options {
  region: string;
  mode: 'modernization' | 'rollout';
  stationName: string;
  rolloutName: string;
  addLog: (msg: string, level: LogEntry['level'], tab: LogEntry['tab']) => void;
}

export function useFileSelection({ region, mode, stationName, rolloutName, addLog }: Options) {
  const [refFiles, setRefFiles] = useState<string[]>([]);
  const [ipFiles, setIpFiles] = useState<string[]>([]);
  const [selectedRef, setSelectedRef] = useState<string | undefined>();
  const [selectedIp, setSelectedIp] = useState<string | undefined>();
  const [refUploadFile, setRefUploadFile] = useState<File | null>(null);
  const [ipUploadFile, setIpUploadFile] = useState<File | null>(null);
  const [sectorFilter, setSectorFilter] = useState<string | null>(null);
  const [modelFilter, setModelFilter] = useState<string | null>(null);
  const [ipPreview, setIpPreview] = useState<IpPreviewData | null>(null);
  const [ipNotFound, setIpNotFound] = useState(false);

  const loadFiles = useCallback(async () => {
    try {
      const [refRes, ipRes] = await Promise.all([listExampleXml(region), listExampleExcel('ip')]);
      const refList = refRes.data.files || [];
      const ipList = ipRes.data.files || [];
      setRefFiles(refList);
      setIpFiles(ipList);
      addLog(`File lists loaded — Region: ${region}, Reference XMLs: ${refList.length}, IP Plans: ${ipList.length}`, 'info', 'system');
      if (ipList.length > 0 && !selectedIp) {
        setSelectedIp(ipList[ipList.length - 1]);
        addLog(`Auto-selected IP Plan: ${ipList[ipList.length - 1]}`, 'info', 'system');
      }
    } catch {
      addLog('Failed to load file lists', 'error', 'system');
    }
  }, [region, addLog, selectedIp]);

  useEffect(() => { loadFiles(); }, [loadFiles]);

  /* ─── IP Plan Preview (with AbortController) ─── */
  const ipLookupName = mode === 'rollout' ? (rolloutName || stationName) : stationName;

  useEffect(() => {
    if (!ipLookupName || !selectedIp) {
      setIpPreview(null);
      setIpNotFound(false);
      return;
    }
    const controller = new AbortController();
    setIpNotFound(false);
    parseIpPlanFromExample(ipLookupName, selectedIp, controller.signal)
      .then(({ data }) => {
        if (controller.signal.aborted) return;
        if (data.success) { setIpPreview(data.data || data); setIpNotFound(false); }
        else { setIpPreview(null); setIpNotFound(true); }
      })
      .catch((err) => {
        if (controller.signal.aborted || axios.isCancel(err)) return;
        setIpPreview(null);
        setIpNotFound(true);
      });
    return () => { controller.abort(); };
  }, [ipLookupName, selectedIp]);

  const filteredRefFiles = refFiles.filter((f) => {
    const upper = f.toUpperCase();
    if (sectorFilter && !upper.includes(sectorFilter)) return false;
    if (modelFilter && !upper.includes(modelFilter)) return false;
    return true;
  });

  return {
    refFiles, ipFiles, filteredRefFiles,
    selectedRef, setSelectedRef,
    selectedIp, setSelectedIp,
    refUploadFile, setRefUploadFile,
    ipUploadFile, setIpUploadFile,
    sectorFilter, setSectorFilter,
    modelFilter, setModelFilter,
    ipPreview, ipNotFound, ipLookupName,
    loadFiles,
  };
}
