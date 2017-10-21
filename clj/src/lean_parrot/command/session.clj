(ns lean-parrot.command.session
  (:require [lean-parrot.util :as u]
            [pandect.core :refer [sha1-hmac]]
            [clojure.string :refer [join]]))

(defmacro session [op & body]
  `(-> {:cmd "session"}
     (assoc :op ~(name op))
     ~@body))

(defn aid [m aid]
  (assoc m :appId aid))

(defn pid [m pid]
  (assoc m :peerId pid))

(defn i [m]
  (assoc m :i (u/uuid)))

(defn signature [m aid pid master-key nonce]
  (let [timestamp (int (/ (System/currentTimeMillis) 1000))
        base      (format "%s:%s::%s:%s" aid pid timestamp nonce)
        sign      (sha1-hmac base master-key)]
    (assoc m :n nonce :t timestamp :s sign)))

(defn session-open [app-id peer-id nonce master-key]
  (session :open
    (aid app-id)
    (pid peer-id)
    (signature app-id peer-id master-key nonce)
    (i)))

(defn session-close [app-id peer-id]
  (session :close
    (aid app-id)
    (pid peer-id)
    (i)))
