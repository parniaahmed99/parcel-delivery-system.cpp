# File: parcel_gui_minimal.py
# Run: python parcel_gui_minimal.py

from __future__ import annotations

import os
import shutil
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk, messagebox, filedialog

CSV_HEADER = [
    "Order_ID",
    "Agent_Age",
    "c2",
    "c3",
    "c4",
    "c5",
    "c6",
    "Order_Date",
    "c8",
    "Pickup_Time",
    "c10",
    "c11",
    "c12",
    "Area",
    "Delivery_Time",
    "Category",
]


@dataclass
class Parcel:
    order_id: str
    agent_age: int
    order_date: str
    pickup_time: str
    area: str
    delivery_time: int
    category: str


def safe_int(s: str) -> int | None:
    s = (s or "").strip()
    if not s:
        return None
    if s.startswith("+"):
        s = s[1:]
    if not s.isdigit():
        return None
    try:
        v = int(s)
    except ValueError:
        return None
    if v < 0:
        return None
    return v


def split_csv_simple(line: str) -> list[str]:
    # Beginner splitter: no quotes handling (matches your C++ split-by-comma).
    return line.rstrip("\r\n").split(",")


class ParcelSystem:
    def __init__(self, csv_file: str) -> None:
        self.csv_file = csv_file
        self.parcels: list[Parcel] = []
        self.pending_queue: list[Parcel] = []
        self.delivered_stack: list[Parcel] = []

    def set_csv_file(self, path: str) -> None:
        self.csv_file = path

    def ensure_header_if_missing(self) -> None:
        if not os.path.exists(self.csv_file) or os.path.getsize(self.csv_file) == 0:
            with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
                f.write(",".join(CSV_HEADER) + "\n")
            return

        with open(self.csv_file, "r", encoding="utf-8", errors="ignore") as f:
            first = f.readline()
        if not first:
            with open(self.csv_file, "w", encoding="utf-8", newline="") as f:
                f.write(",".join(CSV_HEADER) + "\n")

    def load_from_csv(self, max_rows: int = 200) -> None:
        self.ensure_header_if_missing()
        self.parcels.clear()

        try:
            with open(self.csv_file, "r", encoding="utf-8", errors="ignore") as f:
                header = f.readline()
                if not header:
                    return

                loaded = 0
                for raw in f:
                    if loaded >= max_rows:
                        break
                    cols = split_csv_simple(raw)
                    if len(cols) < 16:
                        continue

                    age = safe_int(cols[1])
                    dtime = safe_int(cols[14])
                    if age is None or dtime is None:
                        continue

                    self.parcels.append(
                        Parcel(
                            order_id=cols[0].strip(),
                            agent_age=age,
                            order_date=cols[7].strip(),
                            pickup_time=cols[9].strip(),
                            area=cols[13].strip(),
                            delivery_time=dtime,
                            category=cols[15].strip(),
                        )
                    )
                    loaded += 1
        except FileNotFoundError:
            self.parcels.clear()

    def append_parcel_to_csv(self, p: Parcel) -> None:
        self.ensure_header_if_missing()

        row = [
            p.order_id,
            str(p.agent_age),
            "",
            "",
            "",
            "",
            "",
            p.order_date,
            "",
            p.pickup_time,
            "",
            "",
            "",
            p.area,
            str(p.delivery_time),
            p.category,
        ]

        with open(self.csv_file, "a", encoding="utf-8", newline="") as f:
            f.write(",".join(row) + "\n")

        self.load_from_csv()

    def delete_long_deliveries_from_csv(self, max_time: int) -> int:
        self.ensure_header_if_missing()
        if not os.path.exists(self.csv_file):
            return 0

        tmp_file = self.csv_file + ".tmp"
        deleted = 0

        with open(self.csv_file, "r", encoding="utf-8", errors="ignore") as fin, open(
            tmp_file, "w", encoding="utf-8", newline=""
        ) as fout:
            header = fin.readline()
            fout.write((header.rstrip("\r\n") if header else ",".join(CSV_HEADER)) + "\n")

            for raw in fin:
                cols = split_csv_simple(raw)
                if len(cols) >= 15:
                    dtime = safe_int(cols[14])
                    if dtime is not None and dtime > max_time:
                        deleted += 1
                        continue
                fout.write(raw.rstrip("\r\n") + "\n")

        shutil.move(tmp_file, self.csv_file)

        # Same idea as your C++: reload + clear queue/stack
        self.load_from_csv()
        self.pending_queue.clear()
        self.delivered_stack.clear()

        return deleted

    def find_by_id(self, order_id: str) -> Parcel | None:
        oid = (order_id or "").strip()
        for p in self.parcels:
            if p.order_id == oid:
                return p
        return None

    def fastest(self) -> Parcel | None:
        if not self.parcels:
            return None
        best = self.parcels[0]
        for p in self.parcels:
            if p.delivery_time < best.delivery_time:
                best = p
        return best

    def by_category(self, category: str) -> list[Parcel]:
        cat = (category or "").strip()
        out: list[Parcel] = []
        for p in self.parcels:
            if p.category == cat:
                out.append(p)
        return out

    def enqueue_by_id(self, order_id: str) -> Parcel | None:
        p = self.find_by_id(order_id)
        if not p:
            return None
        self.pending_queue.append(p)
        return p

    def pickup_next(self) -> Parcel | None:
        if not self.pending_queue:
            return None
        p = self.pending_queue.pop(0)
        self.delivered_stack.append(p)
        return p


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Parcel System (Minimal GUI)")
        self.geometry("520x430")
        self.resizable(False, False)

        self.csv_path_var = tk.StringVar(value="amazon_delivery.csv")
        self.system = ParcelSystem(self.csv_path_var.get())
        self.system.load_from_csv()

        self.status_var = tk.StringVar(value=f"Loaded {len(self.system.parcels)} parcels")

        self._build_main()

    def _build_main(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="CSV File:").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.csv_path_var, width=45).grid(row=0, column=1, sticky="w", padx=6)
        ttk.Button(top, text="Browse", command=self._browse_csv).grid(row=0, column=2, sticky="w")
        ttk.Button(top, text="Reload", command=self._reload).grid(row=1, column=2, sticky="w", pady=6)

        ttk.Label(top, textvariable=self.status_var).grid(row=1, column=0, columnspan=2, sticky="w", pady=6)

        menu = ttk.LabelFrame(self, text="Main Menu (each opens a separate window)", padding=10)
        menu.pack(fill="both", expand=True, padx=10, pady=10)

        btns = [
            ("1. Display all parcels", self.open_opt1),
            ("2. Add parcel into file", self.open_opt2),
            ("3. Enqueue parcel for pickup", self.open_opt3),
            ("4. Pickup and deliver", self.open_opt4),
            ("5. View delivered history", self.open_opt5),
            ("6. Delete long deliveries from file", self.open_opt6),
            ("7. Search parcel by Order ID", self.open_opt7),
            ("8. Show fastest parcel", self.open_opt8),
            ("9. Search parcels by Category", self.open_opt9),
        ]

        for i, (text, cmd) in enumerate(btns):
            ttk.Button(menu, text=text, command=cmd).grid(row=i, column=0, sticky="ew", pady=3)

        menu.columnconfigure(0, weight=1)

    def _browse_csv(self) -> None:
        path = filedialog.askopenfilename(
            title="Select CSV file",
            filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
        )
        if not path:
            return
        self.csv_path_var.set(path)
        self._reload()

    def _reload(self) -> None:
        self.system.set_csv_file(self.csv_path_var.get())
        self.system.load_from_csv()
        self.status_var.set(f"Loaded {len(self.system.parcels)} parcels")

    def _info(self, msg: str) -> None:
        self.status_var.set(msg)

    # ---------------- Option windows ----------------

    def open_opt1(self) -> None:
        win = ttk.FrameWindow(self, "Option 1: Display all parcels")
        tree = win.make_table(
            columns=("id", "age", "date", "pickup", "area", "dtime", "cat"),
            headings=("Order ID", "Age", "Order Date", "Pickup Time", "Area", "Delivery Time", "Category"),
            widths=(140, 60, 110, 110, 130, 110, 120),
        )

        def refresh() -> None:
            for item in tree.get_children():
                tree.delete(item)
            for p in self.system.parcels:
                tree.insert("", "end", values=(p.order_id, p.agent_age, p.order_date, p.pickup_time, p.area, p.delivery_time, p.category))
            self._info(f"Displayed {len(self.system.parcels)} parcels")

        ttk.Button(win.body_top, text="Refresh", command=refresh).pack(side="left")
        refresh()

    def open_opt2(self) -> None:
        win = ttk.FrameWindow(self, "Option 2: Add parcel into file (CSV)")
        fields = {
            "Order ID": tk.StringVar(),
            "Agent Age": tk.StringVar(),
            "Order Date": tk.StringVar(),
            "Pickup Time": tk.StringVar(),
            "Area": tk.StringVar(),
            "Delivery Time": tk.StringVar(),
            "Category": tk.StringVar(),
        }

        row = 0
        for label, var in fields.items():
            ttk.Label(win.body, text=label).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(win.body, textvariable=var, width=34).grid(row=row, column=1, sticky="w", pady=4)
            row += 1

        def save() -> None:
            oid = fields["Order ID"].get().strip()
            age = safe_int(fields["Agent Age"].get())
            dtime = safe_int(fields["Delivery Time"].get())
            if not oid:
                messagebox.showerror("Error", "Order ID is required.")
                return
            if age is None:
                messagebox.showerror("Error", "Agent Age must be a valid integer.")
                return
            if dtime is None:
                messagebox.showerror("Error", "Delivery Time must be a valid integer.")
                return

            p = Parcel(
                order_id=oid,
                agent_age=age,
                order_date=fields["Order Date"].get().strip(),
                pickup_time=fields["Pickup Time"].get().strip(),
                area=fields["Area"].get().strip(),
                delivery_time=dtime,
                category=fields["Category"].get().strip(),
            )

            try:
                self.system.append_parcel_to_csv(p)
                self._info(f"Added {oid} to CSV. Total: {len(self.system.parcels)}")
                messagebox.showinfo("Saved", "Parcel saved to CSV successfully.")
            except OSError as e:
                messagebox.showerror("File Error", str(e))

        ttk.Button(win.body_bottom, text="Save to CSV", command=save).pack(side="left")

    def open_opt3(self) -> None:
        win = ttk.FrameWindow(self, "Option 3: Enqueue parcel for pickup")
        oid_var = tk.StringVar()

        ttk.Label(win.body, text="Order ID:").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Entry(win.body, textvariable=oid_var, width=32).grid(row=0, column=1, sticky="w", pady=6)

        lst = tk.Listbox(win.body, height=12, width=58)
        lst.grid(row=2, column=0, columnspan=2, sticky="w", pady=8)

        msg = tk.StringVar(value="")
        ttk.Label(win.body, textvariable=msg).grid(row=3, column=0, columnspan=2, sticky="w")

        def refresh_list() -> None:
            lst.delete(0, tk.END)
            for i, p in enumerate(self.system.pending_queue, start=1):
                lst.insert(tk.END, f"{i}. {p.order_id} | {p.area} | {p.delivery_time} min")

        def enqueue() -> None:
            oid = oid_var.get().strip()
            if not oid:
                msg.set("Enter Order ID.")
                return
            p = self.system.enqueue_by_id(oid)
            if not p:
                msg.set(f"Order ID '{oid}' not found in CSV data.")
                return
            msg.set(f"Enqueued: {p.order_id}")
            self._info(f"Enqueued {p.order_id}")
            refresh_list()

        ttk.Button(win.body_top, text="Enqueue", command=enqueue).pack(side="left")
        ttk.Button(win.body_top, text="Refresh Queue", command=refresh_list).pack(side="left", padx=6)
        refresh_list()

    def open_opt4(self) -> None:
        win = ttk.FrameWindow(self, "Option 4: Pickup and deliver")
        msg = tk.StringVar(value="")

        def pickup() -> None:
            p = self.system.pickup_next()
            if not p:
                msg.set("No pending parcels.")
                self._info("Pickup failed (empty queue)")
                return
            msg.set(f"Picked up + delivered: {p.order_id}")
            self._info(f"Delivered {p.order_id}")

        ttk.Button(win.body, text="Pickup Next", command=pickup).pack(anchor="w", pady=10)
        ttk.Label(win.body, textvariable=msg).pack(anchor="w")

    def open_opt5(self) -> None:
        win = ttk.FrameWindow(self, "Option 5: Delivered history")
        lst = tk.Listbox(win.body, height=14, width=62)
        lst.pack(anchor="w", pady=8)

        def refresh() -> None:
            lst.delete(0, tk.END)
            # latest first
            for i, p in enumerate(reversed(self.system.delivered_stack), start=1):
                lst.insert(tk.END, f"{i}. {p.order_id} | {p.area} | {p.delivery_time} min | {p.order_date}")
            self._info(f"Delivered count: {len(self.system.delivered_stack)}")

        ttk.Button(win.body_top, text="Refresh", command=refresh).pack(side="left")
        refresh()

    def open_opt6(self) -> None:
        win = ttk.FrameWindow(self, "Option 6: Delete long deliveries from file")
        max_var = tk.StringVar()
        msg = tk.StringVar(value="")

        ttk.Label(win.body, text="Max allowed delivery time:").grid(row=0, column=0, sticky="w", pady=8)
        ttk.Entry(win.body, textvariable=max_var, width=16).grid(row=0, column=1, sticky="w", pady=8)

        def run_delete() -> None:
            mt = safe_int(max_var.get())
            if mt is None:
                msg.set("Enter a valid integer.")
                return
            try:
                deleted = self.system.delete_long_deliveries_from_csv(mt)
                msg.set(f"Deleted {deleted} rows from CSV (time > {mt}).")
                self._info(f"Deleted {deleted} from CSV. Reloaded {len(self.system.parcels)} parcels.")
            except OSError as e:
                messagebox.showerror("File Error", str(e))

        ttk.Button(win.body_bottom, text="Delete from CSV", command=run_delete).pack(side="left")
        ttk.Label(win.body, textvariable=msg).grid(row=1, column=0, columnspan=2, sticky="w")

    def open_opt7(self) -> None:
        win = ttk.FrameWindow(self, "Option 7: Search by Order ID")
        oid_var = tk.StringVar()
        out = tk.StringVar(value="")

        ttk.Label(win.body, text="Order ID:").grid(row=0, column=0, sticky="w", pady=8)
        ttk.Entry(win.body, textvariable=oid_var, width=32).grid(row=0, column=1, sticky="w", pady=8)

        def search() -> None:
            p = self.system.find_by_id(oid_var.get().strip())
            if not p:
                out.set("Not found.")
                return
            out.set(
                f"{p.order_id} | Age {p.agent_age} | {p.order_date} | {p.pickup_time} | {p.area} | {p.delivery_time} | {p.category}"
            )
            self._info(f"Found {p.order_id}")

        ttk.Button(win.body_top, text="Search", command=search).pack(side="left")
        ttk.Label(win.body, textvariable=out, wraplength=430).grid(row=1, column=0, columnspan=2, sticky="w")

    def open_opt8(self) -> None:
        win = ttk.FrameWindow(self, "Option 8: Show fastest parcel")
        out = tk.StringVar(value="")

        def run() -> None:
            p = self.system.fastest()
            if not p:
                out.set("No parcels loaded.")
                return
            out.set(f"{p.order_id} | {p.area} | {p.delivery_time} min | {p.order_date} | {p.category}")
            self._info(f"Fastest: {p.order_id}")

        ttk.Button(win.body_top, text="Show Fastest", command=run).pack(side="left")
        ttk.Label(win.body, textvariable=out, wraplength=430).pack(anchor="w", pady=10)
        run()

    def open_opt9(self) -> None:
        win = ttk.FrameWindow(self, "Option 9: Search by Category")
        cat_var = tk.StringVar()

        ttk.Label(win.body, text="Category:").grid(row=0, column=0, sticky="w", pady=8)
        ttk.Entry(win.body, textvariable=cat_var, width=32).grid(row=0, column=1, sticky="w", pady=8)

        tree = win.make_table(
            columns=("id", "area", "date", "dtime"),
            headings=("Order ID", "Area", "Order Date", "Delivery Time"),
            widths=(160, 180, 140, 120),
            height=10,
        )

        def search() -> None:
            for item in tree.get_children():
                tree.delete(item)
            cat = cat_var.get().strip()
            if not cat:
                return
            matches = self.system.by_category(cat)
            for p in matches:
                tree.insert("", "end", values=(p.order_id, p.area, p.order_date, p.delivery_time))
            self._info(f"Category '{cat}': {len(matches)} matches")
            if not matches:
                messagebox.showinfo("No Results", f"No parcels found in category '{cat}'.")

        ttk.Button(win.body_top, text="Search", command=search).pack(side="left")


class FrameWindow:
    """Tiny helper to make minimal consistent option windows."""
    def __init__(self, master: tk.Tk, title: str) -> None:
        self.top = tk.Toplevel(master)
        self.top.title(title)
        self.top.resizable(False, False)

        self.body_top = ttk.Frame(self.top, padding=(10, 10, 10, 0))
        self.body_top.pack(fill="x")

        self.body = ttk.Frame(self.top, padding=10)
        self.body.pack(fill="both", expand=True)

        self.body_bottom = ttk.Frame(self.top, padding=(10, 0, 10, 10))
        self.body_bottom.pack(fill="x")

    def make_table(
        self,
        columns: tuple[str, ...],
        headings: tuple[str, ...],
        widths: tuple[int, ...],
        height: int = 14,
    ) -> ttk.Treeview:
        tree = ttk.Treeview(self.body, columns=columns, show="headings", height=height)
        for col, head, w in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=w, anchor="w")
        y = ttk.Scrollbar(self.body, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=y.set)
        tree.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        return tree


# attach helper name into ttk namespace style
ttk.FrameWindow = FrameWindow  # type: ignore[attr-defined]


if __name__ == "__main__":
    app = App()
    app.mainloop()
