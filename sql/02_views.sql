CREATE OR REPLACE VIEW public.sales AS
SELECT raw.*,
       to_char(to_date(sale_date, 'MM/DD/YYYY'), 'YYYY') year_key,
       to_char(to_date(sale_date, 'MM/DD/YYYY'), 'YYYY-MM') month_key,
       sale_quantity::INTEGER quantity_num,
       sale_total_price::NUMERIC(18, 2) amount_num
FROM public.mock_data raw;
CREATE OR REPLACE VIEW public.products AS
SELECT DISTINCT product_name, product_category, product_price, product_quantity, pet_category, product_weight, product_color, product_size, product_brand, product_material, product_description, product_rating, product_reviews, product_release_date, product_expiry_date FROM public.mock_data;
CREATE OR REPLACE VIEW public.report_customers AS
SELECT 'top_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT customer_email AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY customer_email ORDER BY value DESC, entity LIMIT 10) result
UNION ALL
SELECT 'country_customers' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT customer_country AS entity, '' AS period, COUNT(DISTINCT customer_email) AS value FROM sales  GROUP BY customer_country) result
UNION ALL
SELECT 'average_order' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT customer_email AS entity, '' AS period, AVG(amount_num) AS value FROM sales  GROUP BY customer_email) result;

CREATE OR REPLACE VIEW public.report_products AS
SELECT 'top_quantity' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_name AS entity, '' AS period, SUM(quantity_num) AS value FROM sales  GROUP BY product_name ORDER BY value DESC, entity LIMIT 10) result
UNION ALL
SELECT 'category_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_category AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY product_category) result
UNION ALL
SELECT 'average_rating' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_name entity, '' period, AVG(CAST(product_rating AS DOUBLE PRECISION)) value FROM products GROUP BY product_name) result
UNION ALL
SELECT 'reviews' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_name entity, '' period, SUM(CAST(product_reviews AS BIGINT)) value FROM products GROUP BY product_name) result;

CREATE OR REPLACE VIEW public.report_quality AS
SELECT 'highest_rating' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_name entity, '' period, AVG(CAST(product_rating AS DOUBLE PRECISION)) value FROM products GROUP BY product_name ORDER BY value DESC, entity LIMIT 10) result
UNION ALL
SELECT 'lowest_rating' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_name entity, '' period, AVG(CAST(product_rating AS DOUBLE PRECISION)) value FROM products GROUP BY product_name ORDER BY value ASC, entity LIMIT 10) result
UNION ALL
SELECT 'most_reviews' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT product_name entity, '' period, SUM(CAST(product_reviews AS BIGINT)) value FROM products GROUP BY product_name ORDER BY value DESC, entity LIMIT 10) result
UNION ALL
SELECT 'rating_quantity_correlation' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT 'all' entity, '' period, CORR(rating, quantity) value FROM (SELECT p.product_name, AVG(CAST(p.product_rating AS DOUBLE PRECISION)) rating, q.quantity FROM products p JOIN (SELECT product_name, SUM(quantity_num) quantity FROM sales GROUP BY product_name) q ON p.product_name = q.product_name GROUP BY p.product_name, q.quantity) grouped) result;

CREATE OR REPLACE VIEW public.report_stores AS
SELECT 'top_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT store_email AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY store_email ORDER BY value DESC, entity LIMIT 5) result
UNION ALL
SELECT 'city_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT CONCAT(store_country, ' / ', store_city) AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY CONCAT(store_country, ' / ', store_city)) result
UNION ALL
SELECT 'country_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT store_country AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY store_country) result
UNION ALL
SELECT 'average_order' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT store_email AS entity, '' AS period, AVG(amount_num) AS value FROM sales  GROUP BY store_email) result;

CREATE OR REPLACE VIEW public.report_suppliers AS
SELECT 'top_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT supplier_email AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY supplier_email ORDER BY value DESC, entity LIMIT 5) result
UNION ALL
SELECT 'average_price' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT supplier_email AS entity, '' AS period, AVG(CAST(product_price AS DOUBLE PRECISION)) AS value FROM sales  GROUP BY supplier_email) result
UNION ALL
SELECT 'country_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT supplier_country AS entity, '' AS period, SUM(amount_num) AS value FROM sales  GROUP BY supplier_country) result;

CREATE OR REPLACE VIEW public.report_time AS
SELECT 'month_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT 'all' AS entity, month_key AS period, SUM(amount_num) AS value FROM sales  GROUP BY 'all', month_key) result
UNION ALL
SELECT 'year_revenue' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT 'all' AS entity, year_key AS period, SUM(amount_num) AS value FROM sales  GROUP BY 'all', year_key) result
UNION ALL
SELECT 'month_average_order' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT 'all' AS entity, month_key AS period, AVG(amount_num) AS value FROM sales  GROUP BY 'all', month_key) result
UNION ALL
SELECT 'month_revenue_change' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT 'all' entity, month_key period, revenue - LAG(revenue) OVER (ORDER BY month_key) value FROM (SELECT month_key, SUM(amount_num) revenue FROM sales GROUP BY month_key) months) result
UNION ALL
SELECT 'year_revenue_change' AS metric, entity, period, CAST(value AS DOUBLE PRECISION) AS value FROM (SELECT 'all' entity, year_key period, revenue - LAG(revenue) OVER (ORDER BY year_key) value FROM (SELECT year_key, SUM(amount_num) revenue FROM sales GROUP BY year_key) years) result;

