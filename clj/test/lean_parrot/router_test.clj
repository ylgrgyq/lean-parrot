(ns lean-parrot.router-test
  (:require [clojure.test :refer :all]
            [lean-parrot.router :refer :all]))

(deftest test-get-route
  (let [d-aid "pyon3kvufmleg773ahop2i7zy0tz2rfjx5bh82n7h5jzuwjg"]
    (println (get-server-uri d-aid))))
