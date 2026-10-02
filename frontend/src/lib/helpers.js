export const JENIS_LABEL = { air_limbah: "Air Limbah", emisi: "Emisi Udara", udara_ambien: "Udara Ambien" };
export const JENIS_OPTIONS = [
  { value: "air_limbah", label: "Air Limbah (IPAL / Outlet)" },
  { value: "emisi", label: "Emisi Udara (Cerobong)" },
  { value: "udara_ambien", label: "Udara Ambien" },
];
export const FREKUENSI_OPTIONS = [
  { value: 1, label: "Bulanan (tiap 1 bulan)" },
  { value: 3, label: "Triwulan (tiap 3 bulan)" },
  { value: 6, label: "Semesteran (tiap 6 bulan)" },
  { value: 12, label: "Tahunan (tiap 12 bulan)" },
];
export const ROLE_LABEL = {
  swarna_admin: "Admin PATUH",
  company_admin: "Admin Perusahaan",
  hrga: "HRGA / PIC Lingkungan",
  supervisor: "Supervisor",
};

export function formatDate(iso) {
  if (!iso) return "-";
  try {
    return new Date(iso).toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return iso;
  }
}

export function dueLabel(days) {
  if (days === null || days === undefined) return "Belum ada jadwal";
  if (days < 0) return `Telat ${Math.abs(days)} hari`;
  if (days === 0) return "Jatuh tempo hari ini";
  return `${days} hari lagi`;
}

// returns tailwind classes for a status pill based on remaining days
export function dueTone(days, belumUji) {
  if (belumUji || days === null || days === undefined || days < 0 || days === 0)
    return "bg-[#FEF2F2] text-[#991B1B] border-[#FCA5A5]";
  if (days <= 14) return "bg-[#FFFBEB] text-[#92400E] border-[#FDE68A]";
  return "bg-[#ECFDF5] text-[#065F46] border-[#A7F3D0]";
}
