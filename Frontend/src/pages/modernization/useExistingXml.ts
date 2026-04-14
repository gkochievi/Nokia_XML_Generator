import { useState, useCallback, useRef } from 'react';
import axios from 'axios';
import type { FormInstance } from 'antd';
import { extractBtsName, inspectExistingXml } from '../../api/client';
import type { InspectResult } from '../../api/client';
import type { RadioModule } from '../../types';
import type { LogEntry } from '../../components/DebugConsole';

interface Options {
  region: string;
  form: FormInstance;
  addLog: (msg: string, level: LogEntry['level'], tab: LogEntry['tab']) => void;
}

export function inferModelFilterFromInspect(d: InspectResult['data'] | null): string | null {
  const rmods: RadioModule[] = d?.radioModules || [];
  const counts: Record<string, number> = {};
  for (const rm of rmods) {
    const m = (rm.model || '').toUpperCase();
    if (m === 'AHEGA' || m === 'AHEGB') counts[m] = (counts[m] || 0) + 1;
  }
  let best: string | null = null;
  let bestCount = 0;
  for (const [m, c] of Object.entries(counts)) {
    if (c > bestCount) { best = m; bestCount = c; }
  }
  if (!best && d?.suggestedReference) {
    const s = String(d.suggestedReference).toUpperCase();
    if (s.includes('AHEGB')) best = 'AHEGB';
    else if (s.includes('AHEGA')) best = 'AHEGA';
  }
  return best;
}

export function useExistingXml({ region, form, addLog }: Options) {
  const [existingFile, setExistingFile] = useState<File | null>(null);
  const [stationName, setStationName] = useState('');
  const [inspectData, setInspectData] = useState<InspectResult['data'] | null>(null);
  const [existingXmlParsing, setExistingXmlParsing] = useState(false);
  const [existingXmlParseStep, setExistingXmlParseStep] = useState(0);
  const abortRef = useRef<AbortController | null>(null);

  const handleExistingXmlChange = useCallback(
    async (file: File) => {
      // Abort any in-flight parsing from a previous upload
      if (abortRef.current) abortRef.current.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      setExistingFile(file);
      setStationName('');
      setInspectData(null);
      setExistingXmlParseStep(0);
      setExistingXmlParsing(true);
      addLog(`Existing XML selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`, 'info', 'system');
      addLog(`Uploading: ${file.name}`, 'info', 'extraction');

      try {
        setExistingXmlParseStep(0);
        const nameRes = await extractBtsName(file, controller.signal);
        if (controller.signal.aborted) return;
        if (nameRes.data.success && nameRes.data.btsName) {
          setStationName(nameRes.data.btsName);
          form.setFieldValue('stationName', nameRes.data.btsName);
          addLog(`Station name: ${nameRes.data.btsName}`, 'success', 'extraction');
        }
        setExistingXmlParseStep(1);
      } catch (err) {
        if (controller.signal.aborted || axios.isCancel(err)) return;
        addLog('Could not extract station name', 'warning', 'extraction');
      }

      try {
        setExistingXmlParseStep(1);
        const inspRes = await inspectExistingXml(file, region, controller.signal);
        if (controller.signal.aborted) return;
        if (inspRes.data.success) {
          const d = inspRes.data.data;
          setInspectData(d);
          addLog(`3G: ${d.has3G ? 'YES' : 'NO'}, 4G: ${d.has4G ? 'YES' : 'NO'}, 5G: ${d.has5G ? 'YES' : 'NO'}, Sectors: ${d.sectorCount}`, 'success', 'extraction');
          if (d.suggestedReference) addLog(`Suggested: ${d.suggestedReference}`, 'info', 'extraction');
        }
        setExistingXmlParseStep(2);
      } catch (err) {
        if (controller.signal.aborted || axios.isCancel(err)) return;
        addLog('Could not inspect XML', 'warning', 'extraction');
      } finally {
        if (!controller.signal.aborted) {
          setTimeout(() => {
            if (!controller.signal.aborted) {
              setExistingXmlParsing(false);
              setExistingXmlParseStep(0);
            }
          }, 450);
        }
      }
    },
    [region, form, addLog],
  );

  return {
    existingFile,
    stationName, setStationName,
    inspectData, setInspectData,
    existingXmlParsing, existingXmlParseStep,
    handleExistingXmlChange,
  };
}
