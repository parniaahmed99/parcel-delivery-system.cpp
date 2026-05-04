// File: main.cpp
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

static const int MAX_PARCELS = 200;

static int isDigitChar(char c) { return c >= '0' && c <= '9'; }

static void trimCRLF(char* s) {
    if (!s) return;
    int n = (int)strlen(s);
    while (n > 0 && (s[n - 1] == '\n' || s[n - 1] == '\r')) {
        s[n - 1] = '\0';
        n--;
    }
}

static void flushLine() {
    int ch;
    while ((ch = getchar()) != '\n' && ch != EOF) {}
}

static int readLine(char* buf, int cap) {
    if (!buf || cap <= 1) return 0;
    if (!fgets(buf, cap, stdin)) return 0;
    trimCRLF(buf);
    return 1;
}

static void safeCopy(char* dst, int cap, const char* src) {
    if (!dst || cap <= 0) return;
    if (!src) { dst[0] = '\0'; return; }
    strncpy(dst, src, (size_t)(cap - 1));
    dst[cap - 1] = '\0';
}

static int parseInt(const char* s, int* out) {
    if (!s || !*s) return 0;

    int i = 0;
    if (s[i] == '+') i++;

    if (!isDigitChar(s[i])) return 0;

    long long val = 0;
    for (; s[i]; i++) {
        if (!isDigitChar(s[i])) return 0;
        val = val * 10 + (s[i] - '0');
        if (val > 2147483647LL) return 0;
    }

    *out = (int)val;
    return 1;
}

/* -------------------------- DATA: Parcel (Linked List) -------------------------- */

struct Parcel {
    char orderID[64];
    int agentAge;
    char orderDate[32];
    char pickupTime[32];
    char area[64];
    int deliveryTime;
    char category[64];
    int fromCSV;     // 1 = CSV parcel
    Parcel* next;
};

static Parcel* head = 0;

static void clearAllParcels() {
    Parcel* cur = head;
    while (cur) {
        Parcel* nxt = cur->next;
        delete cur;
        cur = nxt;
    }
    head = 0;
}

static Parcel* addParcelToList(
    const char* id,
    int age,
    const char* date,
    const char* time,
    const char* area,
    int dtime,
    const char* category,
    int fromCSV
) {
    Parcel* p = new Parcel();
    safeCopy(p->orderID, (int)sizeof(p->orderID), id);
    p->agentAge = age;
    safeCopy(p->orderDate, (int)sizeof(p->orderDate), date);
    safeCopy(p->pickupTime, (int)sizeof(p->pickupTime), time);
    safeCopy(p->area, (int)sizeof(p->area), area);
    p->deliveryTime = dtime;
    safeCopy(p->category, (int)sizeof(p->category), category);
    p->fromCSV = fromCSV;
    p->next = 0;

    if (!head) {
        head = p;
        return p;
    }

    Parcel* t = head;
    while (t->next) t = t->next;
    t->next = p;
    return p;
}

/* -------------------------- CSV writing (Option 2) -------------------------- */

static int fileIsEmpty(FILE* f) {
    long cur = ftell(f);
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, cur, SEEK_SET);
    return size == 0;
}

static void ensureCSVHeader(FILE* f) {
    // We keep 16 columns. Program uses indices:
    // 0=id, 1=age, 7=date, 9=time, 13=area, 14=dtime, 15=category
    if (fileIsEmpty(f)) {
        fprintf(f,
            "Order_ID,Agent_Age,c2,c3,c4,c5,c6,Order_Date,c8,Pickup_Time,c10,c11,c12,Area,Delivery_Time,Category\n"
        );
    }
}

static int appendParcelToCSV(
    const char* filename,
    const char* id,
    int age,
    const char* date,
    const char* time,
    const char* area,
    int dtime,
    const char* category
) {
    FILE* f = fopen(filename, "a+");
    if (!f) return 0;

    ensureCSVHeader(f);

    // 16 columns, unused columns blank
    fprintf(f,
        "%s,%d,,,,,,%s,,%s,,,,%s,%d,%s\n",
        id,
        age,
        date,
        time,
        area,
        dtime,
        category
    );

    fclose(f);
    return 1;
}

/* -------------------------- CSV Parsing (simple split by comma) -------------------------- */

static int splitCSV(char* line, char* fields[], int maxFields) {
    trimCRLF(line);
    int count = 0;
    char* p = line;

    while (*p && count < maxFields) {
        fields[count++] = p;
        while (*p && *p != ',') p++;
        if (*p == ',') {
            *p = '\0';
            p++;
        }
    }
    return count;
}

/* -------------------------- Load CSV into memory -------------------------- */

static void loadFromCSV(const char* filename) {
    FILE* f = fopen(filename, "r");
    if (!f) {
        printf("Could not open %s (will be created when you add).\n", filename);
        return;
    }

    char line[4096];
    if (!fgets(line, (int)sizeof(line), f)) {
        fclose(f);
        return;
    }

    int loaded = 0;

    while (fgets(line, (int)sizeof(line), f) && loaded < MAX_PARCELS) {
        char parseLine[4096];
        safeCopy(parseLine, (int)sizeof(parseLine), line);

        char* fields[32];
        int c = splitCSV(parseLine, fields, 32);
        if (c < 16) continue;

        int age = 0, dtime = 0;
        if (!parseInt(fields[1], &age)) continue;
        if (!parseInt(fields[14], &dtime)) continue;

        addParcelToList(fields[0], age, fields[7], fields[9], fields[13], dtime, fields[15], 1);
        loaded++;
    }

    fclose(f);
    printf("Loaded %d parcels from CSV.\n", loaded);
}

/* -------------------------- Option 1: Print ONLY CSV parcels -------------------------- */

static void displayCSVParcelsOnly() {
    printf("\nCSV PARCELS ONLY:\n");
    printf("Order ID | Age | Date | Pickup | Area | Time(min) | Category\n");

    int shown = 0;
    for (Parcel* t = head; t && shown < MAX_PARCELS; t = t->next) {
        if (t->fromCSV == 1) {
            printf("%s | %d | %s | %s | %s | %d | %s\n",
                   t->orderID, t->agentAge, t->orderDate, t->pickupTime,
                   t->area, t->deliveryTime, t->category);
            shown++;
        }
    }

    if (shown == 0) printf("No CSV parcels.\n");
}

/* -------------------------- CSV-only search/fastest/category (7/8/9) -------------------------- */

static Parcel* findCSVParcelByID(const char* id) {
    for (Parcel* t = head; t; t = t->next) {
        if (t->fromCSV == 1 && strcmp(t->orderID, id) == 0) return t;
    }
    return 0;
}

static void searchByOrderID_CSVOnly() {
    char id[64];
    printf("Enter Order ID: ");
    readLine(id, (int)sizeof(id));

    Parcel* p = findCSVParcelByID(id);
    if (!p) {
        printf("Not found in CSV parcels.\n");
        return;
    }

    printf("\nFOUND (CSV):\n");
    printf("Order ID: %s\n", p->orderID);
    printf("Agent Age: %d\n", p->agentAge);
    printf("Order Date: %s\n", p->orderDate);
    printf("Pickup Time: %s\n", p->pickupTime);
    printf("Area: %s\n", p->area);
    printf("Delivery Time: %d min\n", p->deliveryTime);
    printf("Category: %s\n", p->category);
}

static void showFastestParcel_CSVOnly() {
    Parcel* fastest = 0;

    for (Parcel* t = head; t; t = t->next) {
        if (t->fromCSV != 1) continue;
        if (!fastest || t->deliveryTime < fastest->deliveryTime) fastest = t;
    }

    if (!fastest) {
        printf("No CSV parcels.\n");
        return;
    }

    printf("\nFASTEST PARCEL (CSV only):\n");
    printf("Order ID: %s\n", fastest->orderID);
    printf("Area: %s\n", fastest->area);
    printf("Delivery Time: %d min\n", fastest->deliveryTime);
    printf("Date: %s\n", fastest->orderDate);
}

static void searchByCategory_CSVOnly() {
    char cat[64];
    printf("Enter Category: ");
    readLine(cat, (int)sizeof(cat));

    int found = 0;
    printf("\nMATCHES (CSV only):\n");
    for (Parcel* t = head; t; t = t->next) {
        if (t->fromCSV == 1 && strcmp(t->category, cat) == 0) {
            printf("%s | %s | %s | %d min\n",
                   t->orderID, t->area, t->orderDate, t->deliveryTime);
            found++;
        }
    }
    if (found == 0) printf("No CSV parcels in that category.\n");
}

/* -------------------------- Queue (Pending) -------------------------- */

struct QNode {
    Parcel* data;
    QNode* next;
};

static QNode* qFront = 0;
static QNode* qRear = 0;

static void clearQueue() {
    while (qFront) {
        QNode* t = qFront;
        qFront = qFront->next;
        delete t;
    }
    qRear = 0;
}

static void enqueuePending(Parcel* p) {
    if (!p) return;

    QNode* n = new QNode();
    n->data = p;
    n->next = 0;

    if (!qRear) {
        qFront = qRear = n;
        return;
    }

    qRear->next = n;
    qRear = n;
}

static Parcel* dequeuePending() {
    if (!qFront) return 0;

    QNode* t = qFront;
    Parcel* p = t->data;

    qFront = qFront->next;
    if (!qFront) qRear = 0;

    delete t;
    return p;
}

/* -------------------------- Stack (Delivered) -------------------------- */

struct SNode {
    Parcel* data;
    SNode* next;
};

static SNode* sTop = 0;

static void clearStack() {
    while (sTop) {
        SNode* t = sTop;
        sTop = sTop->next;
        delete t;
    }
}

static void pushDelivered(Parcel* p) {
    if (!p) return;

    SNode* n = new SNode();
    n->data = p;
    n->next = sTop;
    sTop = n;
}

static void viewDelivered() {
    printf("\nDELIVERED HISTORY (latest first):\n");
    if (!sTop) {
        printf("None.\n");
        return;
    }

    for (SNode* cur = sTop; cur; cur = cur->next) {
        Parcel* p = cur->data;
        printf("%s | %s | %d min | %s\n", p->orderID, p->orderDate, p->deliveryTime, p->area);
    }
}

/* -------------------------- Enqueue/Deliver (CSV-only) -------------------------- */

static void enqueueParcelByID_CSVOnly() {
    char id[64];
    printf("Enter Order ID to enqueue: ");
    readLine(id, (int)sizeof(id));

    Parcel* p = findCSVParcelByID(id);
    if (!p) {
        printf("Order ID not found in CSV parcels.\n");
        return;
    }

    enqueuePending(p);
    printf("Enqueued %s for pickup.\n", p->orderID);
}

static void pickupNextParcel() {
    Parcel* p = dequeuePending();
    if (!p) {
        printf("No pending parcels.\n");
        return;
    }

    pushDelivered(p);
    printf("Picked up + delivered: %s\n", p->orderID);
}

/* -------------------------- Option 6: Delete from CSV + reload -------------------------- */

static int deleteLongDeliveriesFromCSV(const char* filename, int maxTime, int* deletedOut) {
    *deletedOut = 0;

    FILE* in = fopen(filename, "r");
    if (!in) return 0;

    char tempName[256];
    safeCopy(tempName, (int)sizeof(tempName), filename);
    strncat(tempName, ".tmp", sizeof(tempName) - strlen(tempName) - 1);

    FILE* out = fopen(tempName, "w");
    if (!out) {
        fclose(in);
        return 0;
    }

    char line[4096];

    // Copy header if exists
    if (!fgets(line, (int)sizeof(line), in)) {
        fclose(in);
        fclose(out);
        remove(tempName);
        return 0;
    }
    fputs(line, out);

    while (fgets(line, (int)sizeof(line), in)) {
        // Keep original line for writing
        char originalLine[4096];
        safeCopy(originalLine, (int)sizeof(originalLine), line);

        // Parse a copy
        char parseLine[4096];
        safeCopy(parseLine, (int)sizeof(parseLine), line);

        char* fields[32];
        int c = splitCSV(parseLine, fields, 32);

        if (c >= 15) {
            int dtime = 0;
            if (parseInt(fields[14], &dtime)) {
                if (dtime > maxTime) {
                    (*deletedOut)++;
                    continue; // skip this row
                }
            }
        }

        // Keep row as-is
        fputs(originalLine, out);
        // If original line had no \n at end, ensure newline
        if (strchr(originalLine, '\n') == NULL) fputc('\n', out);
    }

    fclose(in);
    fclose(out);

    // Replace original file
    if (remove(filename) != 0) {
        remove(tempName);
        return 0;
    }
    if (rename(tempName, filename) != 0) {
        return 0;
    }

    return 1;
}

/* -------------------------- MAIN -------------------------- */

int main() {
    const char* CSV_FILE = "amazon_delivery.csv";

    loadFromCSV(CSV_FILE);

    int choice = -1;

    while (choice != 0) {
        printf("\n Parcel System \n");
        printf("1. Display all parcels\n");
        printf("2. Add parcel into file\n");
        printf("3. Enqueue parcel for pickup \n");
        printf("4. Pickup and deliver\n");
        printf("5. View delivered history\n");
        printf("6. Delete long deliveries from file\n");
        printf("7. Search parcel by Order ID \n");
        printf("8. Show fastest parcel\n");
        printf("9. Search parcels by Category \n");
        printf("0. Exit\n");
        printf("Enter choice: ");

        if (scanf("%d", &choice) != 1) {
            printf("Invalid input.\n");
            choice = -1;
            flushLine();
            continue;
        }
        flushLine();

        if (choice == 1) {
            displayCSVParcelsOnly();

        } else if (choice == 2) {
            char id[64], date[32], time[32], area[64], category[64];
            char ageStr[32], dtimeStr[32];
            int age = 0, dtime = 0;

            printf("Order ID: ");
            readLine(id, (int)sizeof(id));

            do {
                printf("Agent Age: ");
                readLine(ageStr, (int)sizeof(ageStr));
            } while (!parseInt(ageStr, &age));

            printf("Order Date: ");
            readLine(date, (int)sizeof(date));

            printf("Pickup Time: ");
            readLine(time, (int)sizeof(time));

            printf("Area: ");
            readLine(area, (int)sizeof(area));

            do {
                printf("Delivery Time (min): ");
                readLine(dtimeStr, (int)sizeof(dtimeStr));
            } while (!parseInt(dtimeStr, &dtime));

            printf("Category: ");
            readLine(category, (int)sizeof(category));

            if (!appendParcelToCSV(CSV_FILE, id, age, date, time, area, dtime, category)) {
                printf("Failed to write to CSV file.\n");
                continue;
            }

            addParcelToList(id, age, date, time, area, dtime, category, 1);
            printf("Parcel saved to CSV and added.\n");

        } else if (choice == 3) {
            enqueueParcelByID_CSVOnly();

        } else if (choice == 4) {
            pickupNextParcel();

        } else if (choice == 5) {
            viewDelivered();

        } else if (choice == 6) {
            char buf[32];
            int maxTime = 0;

            printf("Enter max allowed delivery time: ");
            readLine(buf, (int)sizeof(buf));
            if (!parseInt(buf, &maxTime)) {
                printf("Invalid number.\n");
                continue;
            }

            int deleted = 0;
            if (!deleteLongDeliveriesFromCSV(CSV_FILE, maxTime, &deleted)) {
                printf("Failed to update CSV file.\n");
                continue;
            }

            // Reload memory from updated CSV so everything matches CSV
            clearAllParcels();
            clearQueue();
            clearStack();
            loadFromCSV(CSV_FILE);

            printf("Deleted %d parcels from CSV (Delivery_Time > %d).\n", deleted, maxTime);

        } else if (choice == 7) {
            searchByOrderID_CSVOnly();

        } else if (choice == 8) {
            showFastestParcel_CSVOnly();

        } else if (choice == 9) {
            searchByCategory_CSVOnly();

        } else if (choice == 0) {
            printf("Exiting...\n");

        } else {
            printf("Invalid choice.\n");
        }
    }

    return 0;
}
