export type JobStatus = "queued" | "assigned";

export type DeliveryJob = {
  id: string;
  customer: string;
  address: string;
  priority: number;
  createdAt: string;
  status: JobStatus;
  assignedTo?: string;
};
