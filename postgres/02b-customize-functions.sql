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
CREATE OR REPLACE FUNCTION public.calc_shapes_hypotenuse_length_squared(p_shape_id text)
 RETURNS numeric
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
AS $function$
BEGIN
  RETURN ((SELECT COALESCE(MAX(calc_sides_hypotenuse_length_squared(side_id)), 0) FROM sides WHERE shape = p_shape_id));
END;
$function$;


CREATE OR REPLACE FUNCTION public.calc_sides_length_squared(p_side_id text)
 RETURNS integer
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
AS $function$
BEGIN
  RETURN ((SELECT length FROM sides WHERE side_id = p_side_id) * (SELECT length FROM sides WHERE side_id = p_side_id));
END;
$function$;

CREATE OR REPLACE FUNCTION public.calc_shapes_hypotenuse_length_squared(p_shape_id text)
 RETURNS numeric
 LANGUAGE plpgsql
 STABLE SECURITY DEFINER
AS $function$
BEGIN
  RETURN ((SELECT COALESCE(MAX(calc_sides_hypotenuse_length_squared(side_id)), 0) FROM sides WHERE shape = p_shape_id));
END;
$function$;
