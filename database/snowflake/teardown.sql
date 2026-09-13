/******************************************************************************
 * GNN SUPPLY CHAIN RISK ANALYSIS - TEARDOWN SCRIPT
 * 
 * Purpose: Remove all demo resources
 * 
 * WARNING: This permanently deletes:
 *   - Database SUPPLY_CHAIN_RISK (all data, tables, views, stages, notebooks)
 *   - Warehouse SUPPLY_CHAIN_RISK_WH
 *   - Compute Pool SUPPLY_CHAIN_RISK_COMPUTE_POOL
 *   - External Access Integration SUPPLY_CHAIN_RISK_EXTERNAL_ACCESS
 *   - Git API Integration SUPPLY_CHAIN_RISK_GIT_API_INTEGRATION
 *   - Role SUPPLY_CHAIN_RISK_ROLE
 * 
 * Run as ACCOUNTADMIN to ensure all objects removed.
 ******************************************************************************/

USE ROLE ACCOUNTADMIN;

DROP DATABASE IF EXISTS SUPPLY_CHAIN_RISK;

DROP WAREHOUSE IF EXISTS SUPPLY_CHAIN_RISK_WH;

DROP COMPUTE POOL IF EXISTS SUPPLY_CHAIN_RISK_COMPUTE_POOL;

DROP INTEGRATION IF EXISTS SUPPLY_CHAIN_RISK_EXTERNAL_ACCESS;

DROP INTEGRATION IF EXISTS SUPPLY_CHAIN_RISK_GIT_API_INTEGRATION;

DROP ROLE IF EXISTS SUPPLY_CHAIN_RISK_ROLE;

SELECT 'Cleanup complete!' as STATUS;

/******************************************************************************
 * TEARDOWN COMPLETE
 * 
 * All demo resources have been removed.
 * To redeploy, run scripts/setup_gnn.sql or scripts/setup_networkx.sql
 ******************************************************************************/
