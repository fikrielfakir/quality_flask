import { pgTable, text, serial, integer, boolean, uuid, timestamp, date, time, decimal, jsonb, pgEnum } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { sql } from "drizzle-orm";

// Enums
export const testStatusEnum = pgEnum('test_status', ['Conforme', 'Non-conforme', 'En cours']);
export const defectTypeEnum = pgEnum('defect_type', ['none', 'crack', 'glaze', 'dimension', 'color', 'warping']);
export const userRoleEnum = pgEnum('user_role', ['admin', 'quality_technician', 'production_manager', 'operator']);
export const energySourceEnum = pgEnum('energy_source', ['electricity', 'gas', 'solar', 'other']);
export const wasteTypeEnum = pgEnum('waste_type', ['ceramic', 'glaze', 'packaging', 'chemical', 'water']);

// Core tables
export const profiles = pgTable("profiles", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  email: text("email").unique().notNull(),
  fullName: text("full_name"),
  role: userRoleEnum("role").default('operator'),
  department: text("department"),
  password: text("password").notNull(),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

export const productionLots = pgTable("production_lots", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  lotNumber: text("lot_number").unique().notNull(),
  productionDate: date("production_date").notNull(),
  productType: text("product_type").notNull(),
  quantity: integer("quantity").notNull(),
  operatorId: uuid("operator_id").references(() => profiles.id),
  status: text("status").default('In Production'),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

export const qualityTests = pgTable("quality_tests", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  lotId: uuid("lot_id").references(() => productionLots.id).notNull(),
  testDate: date("test_date").default(sql`CURRENT_DATE`),
  operatorId: uuid("operator_id").references(() => profiles.id),
  lengthMm: decimal("length_mm", { precision: 5, scale: 2 }),
  widthMm: decimal("width_mm", { precision: 5, scale: 2 }),
  thicknessMm: decimal("thickness_mm", { precision: 4, scale: 2 }),
  waterAbsorptionPercent: decimal("water_absorption_percent", { precision: 4, scale: 2 }),
  breakResistanceN: integer("break_resistance_n"),
  defectType: defectTypeEnum("defect_type").default('none'),
  defectCount: integer("defect_count").default(0),
  status: testStatusEnum("status").default('En cours'),
  testType: text("test_type").default('general'),
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

export const energyConsumption = pgTable("energy_consumption", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  recordedDate: date("recorded_date").default(sql`CURRENT_DATE`),
  recordedTime: time("recorded_time").default(sql`CURRENT_TIME`),
  source: energySourceEnum("source").notNull(),
  consumptionKwh: decimal("consumption_kwh", { precision: 10, scale: 2 }).notNull(),
  costAmount: decimal("cost_amount", { precision: 10, scale: 2 }),
  equipmentName: text("equipment_name"),
  department: text("department"),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
});

export const wasteRecords = pgTable("waste_records", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  recordedDate: date("recorded_date").default(sql`CURRENT_DATE`),
  wasteType: wasteTypeEnum("waste_type").notNull(),
  quantityKg: decimal("quantity_kg", { precision: 10, scale: 2 }).notNull(),
  disposalMethod: text("disposal_method"),
  costAmount: decimal("cost_amount", { precision: 10, scale: 2 }),
  responsiblePersonId: uuid("responsible_person_id").references(() => profiles.id),
  notes: text("notes"),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
});

export const complianceDocuments = pgTable("compliance_documents", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  documentName: text("document_name").notNull(),
  documentType: text("document_type").notNull(),
  issueDate: date("issue_date"),
  expiryDate: date("expiry_date"),
  issuingAuthority: text("issuing_authority"),
  status: text("status").default('Active'),
  fileUrl: text("file_url"),
  uploadedBy: uuid("uploaded_by").references(() => profiles.id),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

export const testingCampaigns = pgTable("testing_campaigns", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  campaignName: text("campaign_name").notNull(),
  startDate: date("start_date").notNull(),
  endDate: date("end_date"),
  description: text("description"),
  status: text("status").default('Planning'),
  createdBy: uuid("created_by").references(() => profiles.id),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

// Role-based access control tables
export const appModules = pgTable("app_modules", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  moduleName: text("module_name").notNull().unique(),
  moduleKey: text("module_key").notNull().unique(),
  description: text("description"),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
});

export const permissions = pgTable("permissions", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  permissionName: text("permission_name").notNull(),
  permissionKey: text("permission_key").notNull().unique(),
  moduleId: uuid("module_id").references(() => appModules.id),
  description: text("description"),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
});

export const roles = pgTable("roles", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  roleName: text("role_name").notNull().unique(),
  roleKey: text("role_key").notNull().unique(),
  description: text("description"),
  isSystemRole: boolean("is_system_role").default(false),
  isActive: boolean("is_active").default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

export const rolePermissions = pgTable("role_permissions", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  roleId: uuid("role_id").references(() => roles.id, { onDelete: "cascade" }),
  permissionId: uuid("permission_id").references(() => permissions.id, { onDelete: "cascade" }),
  granted: boolean("granted").default(true),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
});

export const userRoles = pgTable("user_roles", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: uuid("user_id").references(() => profiles.id, { onDelete: "cascade" }).notNull(),
  roleId: uuid("role_id").references(() => roles.id, { onDelete: "cascade" }).notNull(),
  assignedBy: uuid("assigned_by").references(() => profiles.id),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

export const appSettings = pgTable("app_settings", {
  id: uuid("id").primaryKey().default(sql`gen_random_uuid()`),
  settingKey: text("setting_key").notNull().unique(),
  settingValue: jsonb("setting_value").notNull(),
  category: text("category"),
  description: text("description"),
  isSystemSetting: boolean("is_system_setting").default(false),
  updatedBy: uuid("updated_by").references(() => profiles.id),
  createdAt: timestamp("created_at", { withTimezone: true }).default(sql`now()`),
  updatedAt: timestamp("updated_at", { withTimezone: true }).default(sql`now()`),
});

// Legacy users table for compatibility
export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;
