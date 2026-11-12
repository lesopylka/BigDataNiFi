SELECT COUNT(*) sales_count, COUNT(DISTINCT sale_key) unique_sales,
       SUM(sale_quantity::INTEGER) total_quantity,
       SUM(sale_total_price::NUMERIC(18, 2)) total_amount
FROM public.mock_data;
-- Ожидается 10000 продаж после завершения producer и опустошения очередей NiFi.
SELECT source_file, COUNT(*) FROM public.mock_data GROUP BY source_file ORDER BY source_file;
SELECT COUNT(*) invalid_rows FROM public.mock_data
WHERE sale_quantity::INTEGER <= 0 OR sale_total_price::NUMERIC < 0
   OR customer_email = '' OR product_name = '' OR sale_date = '';
SELECT COUNT(*) amount_mismatches FROM public.mock_data
WHERE sale_total_price::NUMERIC <> product_price::NUMERIC * sale_quantity::INTEGER;
