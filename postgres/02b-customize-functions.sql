-- ============================================================================
-- SOURCE: ERBCustomizations table, record: 03b-customize-functions.sql
-- If you see SQL errors below, check this customization in Airtable
-- ============================================================================

-- ============================================================================
-- CUSTOMIZE FUNCTIONS - User-defined calculation functions
-- ============================================================================
-- This file is for YOUR custom PostgreSQL functions that should persist
-- across regeneration of the base ERB files.
--
-- IMPORTANT:
--   - This file runs AFTER 02-create-functions.sql
--   - Base ERB calc functions already exist when this runs
--   - This file will NOT be overwritten by ERB regeneration
--
-- ============================================================================

-- Your custom functions go here:
CREATE OR REPLACE FUNCTION public.calc_roles_all_linked_workflow_steps(p_role_id text)
 RETURNS text
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
AS $function$
BEGIN
  RETURN (SELECT string_agg(DISTINCT calc_workflow_steps_name(workflow_step_id)::text, ', ') FROM workflow_steps WHERE assigned_role = p_role_id);
END;
$function$;

CREATE OR REPLACE FUNCTION public.calc_departments_all_related_workflow_steps(p_department_id text)
 RETURNS text
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
AS $function$
BEGIN
  RETURN (SELECT string_agg(DISTINCT calc_roles_all_linked_workflow_steps(role_id)::text, ', ') FROM roles WHERE owned_by = p_department_id);
END;
$function$;

CREATE OR REPLACE FUNCTION public.calc_departments_all_distinct_workflows_for_owned_roles(p_department_id text)
 RETURNS text
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
AS $function$
BEGIN
  RETURN (SELECT string_agg(DISTINCT calc_roles_distinct_workflows_for_linked_steps(role_id)::text, ', ') FROM roles WHERE owned_by = p_department_id);
END;
$function$;

