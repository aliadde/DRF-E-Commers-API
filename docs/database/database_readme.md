# psotgresql documentation

## Summary

- [Introduction](#introduction)
- [Database Type](#database-type)
- [Table Structure](#table-structure)
  - [users](#users)
  - [addresses](#addresses)
  - [orders](#orders)
  - [order_items](#order_items)
  - [baskets](#baskets)
  - [basket_items](#basket_items)
  - [products](#products)
  - [categories](#categories)
- [Relationships](#relationships)
- [Database Diagram](#database-Diagram)

## Introduction

## Database type

- **Database system:** PostgreSQL

  ## Table structure

### users

| Name                | Type         | Settings                                | References              | Note |
| ------------------- | ------------ | --------------------------------------- | ----------------------- | ---- |
| **id**              | INTEGER      | ?”‘ PK, not null , unique, autoincrement | users_id_fk,users_id_fk |      |
| **username**        | VARCHAR(255) | not null                                |                         |      |
| **email**           | VARCHAR(255) | not null                                |                         |      |
| **hashed_password** | VARCHAR(255) | not null                                |                         |      |

#### Indexes

| Name          | Unique | Fields |
| ------------- | ------ | ------ |
| users_index_0 |        |        |

### addresses

| Name         | Type         | Settings                                | References           | Note |
| ------------ | ------------ | --------------------------------------- | -------------------- | ---- |
| **id**       | INTEGER      | ?”‘ PK, not null , unique, autoincrement | addresses_id_fk      |      |
| **location** | VARCHAR(255) | not null                                |                      |      |
| **user_id**  | INTEGER      | not null                                | addresses_user_id_fk |      |

### orders

| Name           | Type         | Settings                                | References | Note |
| -------------- | ------------ | --------------------------------------- | ---------- | ---- |
| **id**         | INTEGER      | ?”‘ PK, not null , unique, autoincrement |            |      |
| **user_id**    | INTEGER      | not null                                |            |      |
| **created_at** | TIMESTAMPTZ  | not null                                |            |      |
| **updated_at** | TIMESTAMPTZ  | not null                                |            |      |
| **total**      | NUMERIC      | not null                                |            |      |
| **status**     | VARCHAR(255) | not null                                |            |      |
| **address_id** | INTEGER      | not null                                |            |      |

### order_items

| Name           | Type    | Settings                                | References                | Note |
| -------------- | ------- | --------------------------------------- | ------------------------- | ---- |
| **id**         | INTEGER | ?”‘ PK, not null , unique, autoincrement |                           |      |
| **order_id**   | INTEGER | not null                                | order_items_order_id_fk   |      |
| **quantity**   | INTEGER | not null                                |                           |      |
| **total**      | NUMERIC | not null                                |                           |      |
| **product_id** | INTEGER | not null                                | order_items_product_id_fk |      |

### baskets

| Name           | Type        | Settings                                | References         | Note |
| -------------- | ----------- | --------------------------------------- | ------------------ | ---- |
| **id**         | INTEGER     | ?”‘ PK, not null , unique, autoincrement |                    |      |
| **user_id**    | INTEGER     | not null                                | baskets_user_id_fk |      |
| **created_at** | TIMESTAMPTZ | not null                                |                    |      |

### basket_items

| Name           | Type    | Settings                                | References                 | Note |
| -------------- | ------- | --------------------------------------- | -------------------------- | ---- |
| **id**         | INTEGER | ?”‘ PK, not null , unique, autoincrement |                            |      |
| **basket_id**  | INTEGER | not null                                |                            |      |
| **product_id** | INTEGER | not null                                | basket_items_product_id_fk |      |
| **quantity**   | INTEGER | not null                                |                            |      |

### products

| Name            | Type         | Settings                                | References              | Note |
| --------------- | ------------ | --------------------------------------- | ----------------------- | ---- |
| **id**          | INTEGER      | ?”‘ PK, not null , unique, autoincrement |                         |      |
| **name**        | VARCHAR(255) | not null                                |                         |      |
| **description** | TEXT         | not null                                |                         |      |
| **active**      | BOOLEAN      | not null                                |                         |      |
| **price**       | NUMERIC      | not null                                |                         |      |
| **category_id** | INTEGER      | not null                                | products_category_id_fk |      |
| **quantity**    | INTEGER      | not null                                |                         |      |

### categories

| Name     | Type         | Settings                                | References | Note |
| -------- | ------------ | --------------------------------------- | ---------- | ---- |
| **id**   | INTEGER      | ?”‘ PK, not null , unique, autoincrement |            |      |
| **name** | VARCHAR(255) | not null                                |            |      |

## Relationships

- **addresses to users**: many_to_one
- **users to orders**: one_to_many
- **order_items to orders**: many_to_one
- **users to baskets**: one_to_one
- **baskets to basket_items**: one_to_many
- **products to categories**: one_to_many
- **basket_items to products**: many_to_one
- **order_items to products**: many_to_one
- **addresses to orders**: one_to_many
