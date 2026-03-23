import axios from 'axios';

const api = axios.create({ baseURL: '' });

/* ───── Example / Reference Files ───── */

export const listExampleXml = (region: string) =>
  api.get<{ success: boolean; files: string[] }>('/api/example-files/xml', { params: { region } });

export const listExampleExcel = (category = 'ip') =>
  api.get<{ success: boolean; files: string[] }>('/api/example-files/excel', { params: { category } });

export const uploadExampleFile = (file: File, meta: { region?: string; category?: string }) => {
  const fd = new FormData();
  fd.append('file', file);
  if (meta.region) fd.append('region', meta.region);
  if (meta.category) fd.append('category', meta.category);
  return api.post('/api/example-files/upload', fd);
};

export const deleteExampleFile = (filename: string, meta: { region?: string; category?: string }) =>
  api.post('/api/example-files/delete', { filename, ...meta });

/* ───── Generated Files ───── */

export const listGeneratedFiles = () =>
  api.get<{ success: boolean; files: string[]; filesWithMtime?: { name: string; mtime: number; size: number }[] }>('/api/generated-files');

export const deleteGeneratedFile = (filename: string) =>
  api.post('/api/generated-files/delete', { filename });

export const clearGeneratedFiles = () =>
  api.post('/api/generated-files/clear');

export const downloadUrl = (filename: string) => `/download/${encodeURIComponent(filename)}`;

export const previewGenerated = (filename: string) =>
  api.get<{ content: string }>(`/api/preview/${encodeURIComponent(filename)}`);

/* ───── Extraction helpers ───── */

export const extractBtsName = (file: File) => {
  const fd = new FormData();
  fd.append('xmlFile', file);
  return api.post('/api/extract-bts-name', fd);
};

export const extractBtsId = (file: File) => {
  const fd = new FormData();
  fd.append('xmlFile', file);
  return api.post('/api/extract-bts-id', fd);
};

/* ───── Modernization ───── */

export interface InspectResult {
  success: boolean;
  data: {
    has3G: boolean;
    has4G: boolean;
    has5G: boolean;
    sectorCount: number;
    models: string[];
    modelCodes: string[];
    suggestedReference: string | null;
    availableReferences: string[];
  };
}

export const inspectExistingXml = (file: File, region: string) => {
  const fd = new FormData();
  fd.append('existingXml', file);
  fd.append('region', region);
  return api.post<InspectResult>('/api/modernization/inspect', fd);
};

export const generateModernization = (fd: FormData) =>
  api.post('/api/modernization', fd);

/* ───── SFTP ───── */

export const sftpDownload = (query: string) =>
  api.post('/api/sftp-download', { query }, { responseType: 'blob' });

/* ───── XML Viewer ───── */

export const uploadXmls = (files: File[]) => {
  const fd = new FormData();
  files.forEach((f) => fd.append('xmlFiles', f));
  return api.post('/api/upload-xmls', fd);
};

export const listUploadedXmls = () =>
  api.get<{ files: string[] }>('/api/list-xmls');

export const viewXml = (filename: string) =>
  api.get(`/api/view-xml/${encodeURIComponent(filename)}`);

export const deleteUploadedXml = (filename: string) =>
  api.delete(`/api/delete-xml/${encodeURIComponent(filename)}`);

/* ───── IP Plan Preview ───── */

export const parseIpPlanFromExample = (stationName: string, filename: string) =>
  api.get('/api/parse-ip-plan-from-example', { params: { station_name: stationName, filename } });

export default api;
