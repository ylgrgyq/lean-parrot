(ns lean-parrot.util
  (:require [clojure.string :refer [join]]
            [clojure.tools.logging :as log]
            [pandect.core :refer [sha1-hmac]])
  (:import [java.util UUID]))

(defn uuid []
  (str (UUID/randomUUID)))

(defn assoc-some [m & kvs]
  (if-not (even? (count kvs))
    (throw (IllegalArgumentException. "even number of key-values required."))
    (if-let [kvs (not-empty (filter #(some? (second %)) (partition 2 kvs)))]
      (apply assoc m (apply concat kvs))
      m)))

(defn wrap-with-signature [msg aid pid master-key nonce]
  (let [timestamp (int (/ (System/currentTimeMillis) 1000))
        base      (format "%s:%s::%s:%s" aid pid timestamp nonce)
        sign      (sha1-hmac base master-key)]
    (assoc-some msg :appId aid :peerId pid :n nonce :t timestamp :s sign)))
