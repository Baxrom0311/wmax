package com.wmax.mobile_flutter;

import android.content.Context;
import android.content.ContentValues;
import android.content.SharedPreferences;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;
import android.net.Uri;

import com.google.android.gms.wearable.DataEvent;
import com.google.android.gms.wearable.DataEventBuffer;
import com.google.android.gms.wearable.DataMapItem;
import com.google.android.gms.wearable.MessageEvent;
import com.google.android.gms.wearable.Wearable;
import com.google.android.gms.wearable.WearableListenerService;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Set;
import java.security.MessageDigest;
import java.nio.charset.StandardCharsets;
import org.json.JSONObject;

public class WmaxWearDataListenerService extends WearableListenerService {
    private static final String HEALTH_DATA_PATH = "/wmax/health-data";
    private static QueueDatabase queueDatabase;

    @Override
    public void onDataChanged(DataEventBuffer events) {
        try {
            for (DataEvent event : events) {
                if (event.getType() != DataEvent.TYPE_CHANGED) {
                    continue;
                }
                Uri uri = event.getDataItem().getUri();
                if (uri.getPath() == null || !uri.getPath().startsWith(HEALTH_DATA_PATH + "/")) {
                    continue;
                }
                String payload = DataMapItem.fromDataItem(event.getDataItem()).getDataMap().getString("payload");
                if (payload != null && !payload.trim().isEmpty() && enqueuePayload(this, payload)) {
                    Wearable.getDataClient(this).deleteDataItems(uri);
                }
            }
        } finally {
            events.release();
        }
    }

    static ArrayList<String> getQueuedPayloads(Context context) {
        synchronized (WmaxWearDataListenerService.class) {
            SQLiteDatabase db = database(context);
            ArrayList<String> payloads = new ArrayList<>();
            try (android.database.Cursor cursor = db.query(
                    "wear_payloads",
                    new String[]{"payload"},
                    null,
                    null,
                    null,
                    null,
                    "id ASC")) {
                while (cursor.moveToNext()) payloads.add(cursor.getString(0));
            }
            return payloads;
        }
    }

    static void acknowledgePayloads(Context context, ArrayList<String> acknowledged) {
        if (acknowledged == null || acknowledged.isEmpty()) {
            return;
        }
        synchronized (WmaxWearDataListenerService.class) {
            SQLiteDatabase db = database(context);
            db.beginTransaction();
            try {
                for (String payload : acknowledged) {
                    db.delete("wear_payloads", "payload = ?", new String[]{payload});
                }
                db.setTransactionSuccessful();
            } finally {
                db.endTransaction();
            }
        }
    }

    public static boolean enqueuePayload(Context context, String payload) {
        synchronized (WmaxWearDataListenerService.class) {
            try {
                JSONObject body = new JSONObject(payload);
                String batchId = body.optString("batch_id", "");
                if (batchId.isEmpty()) batchId = payloadKey(payload);
                ContentValues values = new ContentValues();
                values.put("batch_id", batchId);
                values.put("payload", payload);
                SQLiteDatabase db = database(context);
                long inserted = db.insertWithOnConflict(
                        "wear_payloads", null, values, SQLiteDatabase.CONFLICT_IGNORE);
                if (inserted >= 0) return true;
                try (android.database.Cursor cursor = db.query(
                        "wear_payloads",
                        new String[]{"payload"},
                        "batch_id = ?",
                        new String[]{batchId},
                        null,
                        null,
                        null,
                        "1")) {
                    return cursor.moveToFirst() && payload.equals(cursor.getString(0));
                }
            } catch (Exception error) {
                android.util.Log.e("WmaxWearData", "Invalid wearable health payload", error);
                return false;
            }
        }
    }

    private static SQLiteDatabase database(Context context) {
        if (queueDatabase == null) {
            queueDatabase = new QueueDatabase(context.getApplicationContext());
        }
        SQLiteDatabase db = queueDatabase.getWritableDatabase();
        migrateLegacyQueue(context.getApplicationContext(), db);
        return db;
    }

    private static void migrateLegacyQueue(Context context, SQLiteDatabase db) {
        SharedPreferences prefs = context.getSharedPreferences("wmax_wear_queue", Context.MODE_PRIVATE);
        if (prefs.getBoolean("sqlite_migrated", false)) return;
        Set<String> oldPayloads = prefs.getStringSet("payloads", new HashSet<>());
        db.beginTransaction();
        try {
            if (oldPayloads != null) {
                for (String payload : oldPayloads) {
                    try {
                        String batchId = new JSONObject(payload).optString("batch_id", "");
                        if (batchId.isEmpty()) batchId = payloadKey(payload);
                        ContentValues values = new ContentValues();
                        values.put("batch_id", batchId);
                        values.put("payload", payload);
                        db.insertWithOnConflict(
                                "wear_payloads", null, values, SQLiteDatabase.CONFLICT_IGNORE);
                    } catch (Exception error) {
                        android.util.Log.e("WmaxWearData", "Could not migrate queued health payload", error);
                    }
                }
            }
            db.setTransactionSuccessful();
        } finally {
            db.endTransaction();
        }
        prefs.edit().putBoolean("sqlite_migrated", true).commit();
    }

    private static String payloadKey(String payload) throws Exception {
        byte[] digest = MessageDigest.getInstance("SHA-256")
                .digest(payload.getBytes(StandardCharsets.UTF_8));
        StringBuilder key = new StringBuilder(digest.length * 2);
        for (byte value : digest) key.append(String.format("%02x", value & 0xff));
        return key.toString();
    }

    private static final class QueueDatabase extends SQLiteOpenHelper {
        QueueDatabase(Context context) {
            super(context, "wmax_wear_queue.db", null, 1);
        }

        @Override
        public void onCreate(SQLiteDatabase db) {
            db.execSQL("CREATE TABLE wear_payloads (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "batch_id TEXT NOT NULL UNIQUE, " +
                    "payload TEXT NOT NULL)");
        }

        @Override
        public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) { }
    }

    @Override
    public void onMessageReceived(MessageEvent messageEvent) {
        if (!HEALTH_DATA_PATH.equals(messageEvent.getPath())) {
            return;
        }
        String payload = new String(messageEvent.getData(), StandardCharsets.UTF_8);
        if (payload.trim().isEmpty()) {
            return;
        }
        enqueuePayload(this, payload);
    }
}
