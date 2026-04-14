import { useState, useEffect, useCallback, useRef } from 'react';
import type { FormInstance } from 'antd';
import { message, Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { generateModernization, listGeneratedFiles, downloadUrl } from '../../api/client';
import type { GenerationResponse } from '../../types';
import type { LogEntry } from '../../components/DebugConsole';

interface Options {
  form: FormInstance;
  mode: 'modernization' | 'rollout';
  region: string;
  existingFile: File | null;
  stationName: string;
  selectedRef: string | undefined;
  refUploadFile: File | null;
  selectedIp: string | undefined;
  ipUploadFile: File | null;
  addLog: (msg: string, level: LogEntry['level'], tab: LogEntry['tab']) => void;
}

function logGenerationDetails(
  data: GenerationResponse,
  addLog: (msg: string, level: LogEntry['level'], tab: LogEntry['tab']) => void,
) {
  addLog('\u2713 XML generated successfully!', 'success', 'generation');
  addLog(`Filename: ${data.filename}`, 'success', 'generation');
  const d = data.details;
  if (!d) return;

  addLog(`--- Replacement Details (${d.mode === 'rollout' ? 'Rollout' : 'Modernization'}) ---`, 'info', 'generation');
  if (d.mode === 'rollout' && d.rollout_overrides) {
    addLog(`Override Name: ${d.rollout_overrides.name || '-'}`, 'info', 'generation');
    addLog(`Override ID: ${d.rollout_overrides.id || '-'}`, 'info', 'generation');
    addLog(`Override TAC: ${d.rollout_overrides.tac || '-'}`, 'info', 'generation');
  }
  addLog(`Reference Name: "${d.reference_bts_name || '-'}"`, 'info', 'generation');
  addLog(`Target Name: "${d.existing_bts_name || '-'}"`, 'info', 'generation');
  addLog(`Name Replacement: ${d.replacement_performed ? 'YES' : 'NO'}`, d.replacement_performed ? 'success' : 'warning', 'generation');
  addLog(`Reference BTS ID: "${d.reference_bts_id || 'N/A'}"`, 'info', 'generation');
  addLog(`Target BTS ID: "${d.existing_bts_id || 'N/A'}"`, 'info', 'generation');
  addLog(`BTS ID Replacement: ${d.bts_id_replacement_performed ? 'YES' : 'NO'}`, d.bts_id_replacement_performed ? 'success' : 'warning', 'generation');
  if (typeof d.ip_plan_found !== 'undefined') {
    addLog(`IP Plan lookup (${d.ip_plan_lookup_station || '-'}): ${d.ip_plan_found ? 'FOUND' : 'NOT FOUND'}`, d.ip_plan_found ? 'success' : 'warning', 'generation');
  }
  addLog(`sctpPortMin: ref="${d.reference_sctp_port || 'N/A'}" \u2192 target="${d.existing_sctp_port || 'N/A'}" | Replaced: ${d.sctp_port_replacement_performed ? 'YES' : 'NO'}`, d.sctp_port_replacement_performed ? 'success' : 'info', 'generation');
  if (d.params_2g_replacement_performed && d.existing_2g_params && d.reference_2g_params) {
    addLog('2G Parameters Replaced:', 'success', 'generation');
    Object.entries(d.existing_2g_params).forEach(([key, value]) => {
      const old = d.reference_2g_params?.[key];
      if (old) addLog(`  ${key}: "${old}" \u2192 "${value}"`, 'success', 'generation');
    });
  } else {
    addLog(`2G Replacement: ${d.params_2g_replacement_performed ? 'YES' : 'NO (no 2G)'}`, 'info', 'generation');
  }
  addLog(`4G Cells: ${d.cells_4g_replacement_performed ? 'YES' : 'NO'} | 4G RootSeq: ${d.rootseq_4g_replacement_performed ? 'YES' : 'NO'} | 5G NR: ${d.nrcells_5g_replacement_performed ? 'YES' : 'NO'}`, d.cells_4g_replacement_performed || d.nrcells_5g_replacement_performed ? 'success' : 'info', 'generation');
  addLog('--- End Replacement Details ---', 'info', 'generation');

  if (data.debug_log?.length) {
    addLog('--- Backend Debug Log ---', 'info', 'generation');
    data.debug_log.forEach((msg: string) => {
      if (typeof msg !== 'string') return;
      if (msg.startsWith('\u2713')) addLog(msg, 'success', 'generation');
      else if (msg.startsWith('\u2717')) addLog(msg, 'error', 'generation');
      else if (msg.startsWith('\u25CB') || msg.toLowerCase().includes('warning')) addLog(msg, 'warning', 'generation');
      else addLog(msg, 'info', 'generation');
    });
    addLog('--- End Backend Debug Log ---', 'info', 'generation');
  }
}

export function useGeneration(options: Options) {
  const { t } = useTranslation();
  const { form, mode, region, existingFile, stationName, selectedRef, refUploadFile, selectedIp, ipUploadFile, addLog } = options;

  const [generating, setGenerating] = useState(false);
  const [popupOpen, setPopupOpen] = useState(false);
  const [popupStep, setPopupStep] = useState(0);
  const [recentFiles, setRecentFiles] = useState<{ name: string; mtime?: number; size?: number }[]>([]);
  const [genRefreshSignal, setGenRefreshSignal] = useState(0);
  const runIdRef = useRef(0);

  const loadRecentFiles = useCallback(async () => {
    try {
      const { data } = await listGeneratedFiles();
      setRecentFiles((data.filesWithMtime || []).slice(0, 5));
    } catch { /* non-critical, silent fail */ }
  }, []);

  useEffect(() => { loadRecentFiles(); }, [loadRecentFiles]);

  const handleGenerate = async () => {
    try { await form.validateFields(); } catch { return; }
    if (mode === 'modernization' && !existingFile) { message.warning(t('existingXmlHelp')); return; }
    if (mode === 'rollout' && !selectedRef && !refUploadFile) { message.warning('Please select a Reference XML'); return; }

    const runId = ++runIdRef.current;
    setPopupOpen(true);
    setPopupStep(0);
    setGenerating(true);

    const logName = mode === 'rollout' ? (form.getFieldValue('rolloutName') || stationName || '-') : (stationName || '-');
    addLog('Starting XML generation...', 'info', 'generation');
    addLog(`Station: "${logName}"`, 'info', 'generation');
    addLog(`Reference 5G XML: ${selectedRef || refUploadFile?.name || '-'}`, 'info', 'generation');
    addLog(`IP Plan: ${selectedIp || ipUploadFile?.name || '-'}`, 'info', 'generation');
    addLog(`Mode: ${mode === 'rollout' ? 'Rollout' : 'Modernization'}`, 'info', 'generation');
    addLog('Sending data to server...', 'info', 'generation');

    const fd = new FormData();
    const effectiveName = mode === 'rollout' ? (form.getFieldValue('rolloutName') || stationName || '') : (stationName || '');
    fd.append('stationName', effectiveName);
    fd.append('mode', mode);
    fd.append('region', region);

    if (mode === 'rollout') {
      if (refUploadFile) {
        fd.append('existingXml', refUploadFile);
        fd.append('reference5gXmlUpload', refUploadFile);
      } else if (selectedRef) {
        fd.append('reference5gXmlSelection', selectedRef);
        fd.append('existingXmlSelection', selectedRef);
      }
    } else {
      fd.append('existingXml', existingFile!);
      if (refUploadFile) fd.append('reference5gXmlUpload', refUploadFile);
      else if (selectedRef) fd.append('reference5gXmlSelection', selectedRef);
    }

    if (ipUploadFile) fd.append('ipPlanUpload', ipUploadFile);
    else if (selectedIp) fd.append('ipPlanSelection', selectedIp);
    if (mode === 'rollout') {
      fd.append('rolloutId', form.getFieldValue('rolloutId') || '');
      fd.append('rolloutName', form.getFieldValue('rolloutName') || '');
      fd.append('rolloutTac', form.getFieldValue('rolloutTac') || '');
    }

    try {
      setPopupStep(1);
      const res = await generateModernization(fd);
      const data = res.data;
      addLog('Server response received', 'info', 'generation');

      if (data.success) {
        logGenerationDetails(data, addLog);

        const doDownload = () => {
          addLog(t('autoDownload'), 'info', 'generation');
          setPopupStep(2);
          if (runIdRef.current !== runId) return;
          const link = document.createElement('a');
          link.href = downloadUrl(data.filename);
          link.download = data.filename;
          link.click();
          addLog(`${t('generationSuccess')} ${data.filename}`, 'success', 'generation');
          message.success(`${t('generationSuccess')} ${data.filename}`);
          loadRecentFiles();
          setGenRefreshSignal((v) => v + 1);
          setTimeout(() => {
            if (runIdRef.current !== runId) return;
            setPopupOpen(false);
            setPopupStep(0);
          }, 500);
        };

        if (data.warnings?.ip_plan) {
          const d = data.details;
          addLog(`\u26A0 ${data.warnings.ip_plan}`, 'warning', 'generation');
          const lookupStation = d?.ip_plan_lookup_station || stationName || '?';
          Modal.confirm({
            title: <span style={{ color: '#fbbf24' }}>{t('ipPlanWarningTitle')}</span>,
            icon: <ExclamationCircleOutlined style={{ color: '#fbbf24' }} />,
            content: (
              <div style={{ color: '#d0d0e8' }}>
                <p style={{ marginBottom: 6 }}><strong style={{ color: '#c4b5fd' }}>{lookupStation}</strong>{' — '}VLAN / IP / Gateway replacements were skipped.</p>
                <p style={{ color: '#b0b0c8' }}>{t('ipPlanConfirm')}</p>
              </div>
            ),
            okText: t('yes'), cancelText: t('no'),
            onOk: doDownload,
            onCancel: () => {
              addLog('User cancelled — IP Plan not found', 'warning', 'generation');
              if (runIdRef.current !== runId) return;
              setPopupOpen(false);
              setPopupStep(0);
            },
          });
        } else {
          doDownload();
        }
      } else {
        addLog(`\u2717 Error: ${data.error}`, 'error', 'generation');
        setPopupOpen(false);
        setPopupStep(0);
        message.error(data.error || 'Generation failed');
      }
    } catch (err: unknown) {
      addLog(`\u2717 Network error: ${err instanceof Error ? err.message : String(err)}`, 'error', 'generation');
      if (runIdRef.current === runId) {
        setPopupOpen(false);
        setPopupStep(0);
      }
      message.error('Generation failed');
    }

    addLog('Generation process finished', 'info', 'generation');
    setGenerating(false);
  };

  return {
    generating,
    popupOpen, popupStep,
    recentFiles, genRefreshSignal,
    handleGenerate, loadRecentFiles,
  };
}
