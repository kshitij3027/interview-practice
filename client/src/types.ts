export type DeliveryJob = {
  id: string;
  customer: string;
  address: string;
  priority: number;
  createdAt: string;
  status: "queued" | "assigned";
  assignedTo?: string;
};
