# parcel-delivery-system.cpp


## Overview
This is a console-based Parcel Delivery Management System developed in C++ and GUI in python
It simulates real-world delivery operations using core Data Structures and File Handling with CSV storage.

The system efficiently manages parcel records, delivery processing, and tracking using **Linked List, Queue, and Stack**.

---

## Features

- Load parcel data from CSV file
- Add new parcels and save them to file
- Search parcel by Order ID
- Find the fastest delivery parcel
- Filter parcels by category
- Delete parcels based on delivery time limit
- Queue system for pending deliveries (FIFO)
- Stack system for delivered parcels history (LIFO)

---

## Data Structures Used

- **Linked List** → Stores parcel records dynamically
- **Queue** → Manages pending deliveries
- **Stack** → Tracks delivered parcel history

---

## Technologies Used

- C++
- File Handling (CSV)
- Dynamic Memory Allocation
- Data Structures (Linked List, Stack, Queue)

---

## Project Files

- `project.cpp` → Complete source code
- `amazon_delivery.csv` → Dataset used for parcel records

---

## How to Run

### 1. Compile the program
```bash
g++ project.cpp -o parcel
