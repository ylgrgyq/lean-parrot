(ns lean-parrot.connection-test
  (:require [clojure.test :refer :all]
            [lean-parrot.connection :refer :all]
            [lean-parrot.command.session :refer :all]
            [lean-parrot.config :as config])
  (:import (io.netty.channel ChannelFuture)))

(deftest test-connect
  (let [open-msg (session-open config/aid "pid" "Hi" config/master-key)
        ^ChannelFuture future (connect {:ping-interval-ms 2000})]
    (println open-msg)
    (.awaitUninterruptibly future 5000)
    (let [future (send! open-msg)]
      (.awaitUninterruptibly future 5000)
      (if (.isSuccess future)
        (println "send succ")
        (println "send failed" (.cause future))))
    (Thread/sleep 5000)
    (disconnect)))
