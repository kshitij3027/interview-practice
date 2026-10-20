import { readFileSync } from 'node:fs';

export class DomainError extends Error {
  constructor(status, code, message, details = {}) {
    super(message);
    this.name = 'DomainError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

export function paidMinutes(shift) {
  const elapsed = (Date.parse(shift.endAt) - Date.parse(shift.startAt)) / 60000;
  const unpaid = shift.breaks.reduce((sum, interval) =>
    sum + (Date.parse(interval.endAt) - Date.parse(interval.startAt)) / 60000, 0);
  return elapsed - unpaid;
}

export function loadFixture(path = new URL('../fixtures/workspace.json', import.meta.url)) {
  const seed = JSON.parse(readFileSync(path, 'utf8'));
  const epoch = Date.parse(seed.seedAt);
  const iso = (minute) => new Date(epoch + minute * 60000).toISOString().replace('.000Z', 'Z');
  const employees = [
    { id: 'emp-21', name: 'Operator 1', facility: seed.facilityLabels[0], role: 'Associate', active: true },
    { id: 'emp-22', name: 'Operator 2', facility: seed.facilityLabels[1], role: 'Operations Lead', active: true },
    { id: 'emp-23', name: 'Operator 3', facility: seed.facilityLabels[0], role: 'Specialist', active: true },
  ];
  const shifts = [];
  function sample(id, employeeId, status, start, end, breaks, note = '', revision = 0) {
    shifts.push({
      id, employeeId, status, startAt: iso(start), endAt: iso(end),
      breaks: breaks.map(([a, b]) => ({ startAt: iso(a), endAt: iso(b) })), note, revision,
    });
  }
  for (let day = 0; day < 5; day += 1) {
    const start = day * 1440 + 900;
    const finish = start + (day === 4 ? 540 : 480);
    const breakStart = start + (day === 0 || day === 3 || day === 4 ? 240 : 270);
    sample(`sh-${301 + day}`, 'emp-21', 'approved', start, finish,
      [[breakStart, breakStart + 30]],
      ['Stock count', '', '', 'Supervisor verified', 'Late trailer'][day],
      [2, 1, 0, 1, 1][day]);
  }
  sample('sh-306', 'emp-22', 'approved', 6 * 1440 + 1410, 7 * 1440 + 480,
    [[7 * 1440 + 15, 7 * 1440 + 45]], 'Overnight handoff', 1);
  sample('sh-307', 'emp-22', 'draft', 8 * 1440 + 480, 8 * 1440 + 960, [], 'Awaiting approval');
  sample('sh-308', 'emp-21', 'approved', 7 * 1440 + 900, 7 * 1440 + 1380, []);
  sample('sh-309', 'emp-23', 'approved', 7 * 1440 + 900, 7 * 1440 + 1380,
    [[7 * 1440 + 1140, 7 * 1440 + 1160]], '', 2);
  sample('sh-310', 'emp-22', 'void', 7 * 1440 + 840, 7 * 1440 + 1080, [], 'Duplicate import', 1);
  sample('sh-311', 'emp-23', 'draft', 6 * 1440 + 600, 6 * 1440 + 840, [], 'Needs signature');
  return { employees, shifts };
}

export function createStore(fixture = loadFixture()) {
  const data = structuredClone(fixture);
  const employees = new Map(data.employees.map((employee) => [employee.id, employee]));
  const shifts = new Map(data.shifts.map((shift) => [shift.id, shift]));
  let datasetRevision = 1;

  function present(shift) {
    return { ...structuredClone(shift), employee: structuredClone(employees.get(shift.employeeId)), paidMinutes: paidMinutes(shift) };
  }

  function getShift(id) {
    const shift = shifts.get(id);
    if (!shift) throw new DomainError(404, 'shift_not_found', 'Shift not found', { shiftId: id });
    return { shift: present(shift), datasetRevision };
  }

  function listShifts(filters = {}) {
    const { employeeId = '', status = '', q = '' } = filters;
    const validStatuses = ['', 'approved', 'draft', 'void'];
    if (!validStatuses.includes(status)) throw new DomainError(400, 'invalid_status', 'Unsupported status filter');
    const search = String(q).trim().toLowerCase();
    const matches = [...shifts.values()].filter((shift) => {
      const employee = employees.get(shift.employeeId);
      return (!employeeId || shift.employeeId === employeeId) &&
        (!status || shift.status === status) &&
        (!search || [shift.id, employee.name, employee.facility, shift.note].some((value) => value.toLowerCase().includes(search)));
    }).sort((a, b) => Date.parse(b.startAt) - Date.parse(a.startAt) || a.id.localeCompare(b.id));
    return { shifts: matches.map(present), datasetRevision };
  }

  async function saveNote(id, input) {
    if (!input || typeof input.note !== 'string' || input.note.length > 400 ||
        !Number.isSafeInteger(input.expectedRevision) || input.expectedRevision < 0) {
      throw new DomainError(400, 'invalid_note', 'Note and expectedRevision are required');
    }
    const delayMs = input.delayMs ?? 0;
    if (!Number.isInteger(delayMs) || delayMs < 0 || delayMs > 1200) {
      throw new DomainError(400, 'invalid_delay', 'delayMs must be 0 to 1200');
    }
    getShift(id);
    if (delayMs) await new Promise((resolve) => setTimeout(resolve, delayMs));
    const shift = shifts.get(id);
    if (shift.revision !== input.expectedRevision) {
      throw new DomainError(409, 'stale_revision', 'Shift changed; reload before saving', { currentRevision: shift.revision });
    }
    const next = input.note.trim();
    const changed = shift.note !== next;
    if (changed) {
      shift.note = next;
      shift.revision += 1;
      datasetRevision += 1;
    }
    return { ...getShift(id), changed };
  }

  return {
    employees: () => ({ employees: structuredClone(data.employees), datasetRevision }),
    listShifts,
    getShift,
    saveNote,
  };
}
