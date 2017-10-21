(defproject lean-parrot "0.1.0-SNAPSHOT"
  :description "FIXME: write description"
  :url "http://example.com/FIXME"
  :license {:name "Eclipse Public License"
            :url "http://www.eclipse.org/legal/epl-v10.html"}
  :dependencies [[org.clojure/clojure "1.8.0"]
                 [org.clojure/tools.nrepl "0.2.12"]
                 [org.clojure/tools.logging "0.3.0"]
                 [org.clojure/data.json "0.2.5"]
                 [clj-http "2.0.1"]

                 [io.netty/netty-all "4.1.6.Final"]
                 [environ "0.5.0"]
                 [pandect "0.3.4"]]
  :main ^:skip-aot lean-parrot.core
  :target-path "target/%s"
  :profiles {:uberjar {:aot :all}}
  :javac-options ["-target" "1.8" "-source" "1.8"])
