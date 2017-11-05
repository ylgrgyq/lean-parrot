(ns lean-parrot.router
  (:require [clj-http.client :as http]
            [clojure.data.json :as json])
  (:import (java.net URI)))

(def router-url "http://router.g0.push.leancloud.cn/v1/route")

(defn get-server-uri [app-id]
  (let [{:keys [status body]} (http/get router-url
                                {:query-params   {:appId app-id}
                                 :content-type   :json
                                 :accept         :json
                                 :socket-timeout 1000
                                 :conn-timeout   1000})]
    (when (= 200 status)
      (when-let [server-addr (:server (json/read-str body :key-fn keyword))]
        (URI. server-addr)))))
