// Tipos que reflejan el esquema real de la BD (backend/app/models).

export interface Product {
  id: string;
  merchant_id: string;
  name: string;
  description: string | null;
  price: string; // Numeric(10,2) llega como string desde PostgREST
  stock: number;
  image_url: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Merchant {
  id: string;
  name: string;
  email: string;
  plan: "free" | "basic" | "pro";
  is_active: boolean;
  business_name: string | null;
  business_hours: string | null;
  business_location: string | null;
  welcome_message: string | null;
  created_at: string;
  updated_at: string;
}

export type OrderStatus =
  | "pending"
  | "paid"
  | "preparing"
  | "delivered"
  | "cancelled";

export interface OrderItem {
  id: string;
  order_id: string;
  product_id: string;
  quantity: number;
  unit_price: string;
  product: { name: string } | null; // embed PostgREST
}

export interface Order {
  id: string;
  merchant_id: string;
  conversation_id: string;
  status: OrderStatus;
  total_amount: string;
  payment_qr_url: string | null;
  payment_reference: string | null;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
  conversation: {
    customer_name: string | null;
    channel: string;
    external_id: string;
  } | null;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  merchant_id: string;
  channel: string; // whatsapp, messenger
  external_id: string;
  customer_name: string | null;
  status: "active" | "closed" | "handoff";
  created_at: string;
  updated_at: string;
  messages: Message[];
}
