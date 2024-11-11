let eventSource;

        function remove_concepts() {
            // Remove concepts IDs from query field
            var target_output = document.getElementById("query");
            target_output.value=target_output.value.replace(/ c[0-9]+/g,"");
        }

        function chat(){
            // Make the "Please wait" container visible
            document.getElementById("waiter").style.display = "block";
            if (!window.EventSource) {
                // IE or an old browser
                alert("Désolé : version trop ancienne de votre navigateur Web.");
            }
            // History Window
            var history_output = document.getElementById("history");
            // Response Window
            var target_output = document.getElementById("response");
            // Please Wait message
            var waiter = document.getElementById("waiter");
            // Input query
            var query_input = document.getElementById("query");
            if (query_input.type == "file"){
                target_output.innerHTML="<h1>Pardon ? Merci de poser une question !</h1>";
                // Hide "Please Wait"
                waiter.style.display = "none";
                return;
            }
            // Remove concept ID's from query (not useful during chat)
            remove_concepts();
            query = query_input.value + " " + document.getElementById("docs").value
            if (query == ""){
                target_output.innerHTML="<h1>Pardon ? Merci de poser une question !</h1>";
                // Hide "Please Wait"
                waiter.style.display = "none";
                return;
            }
            // Call Patchat and get an EventSource (stream) object in response
            var answer_source = new EventSource("/answer?query="+ encodeURIComponent(query));
            answer_source.onmessage = function (e) {
                if (e.data == "open"){
                    // copy current output block to history block
                    history_output.innerHTML+=target_output.innerHTML;
                    // clear current output
                    target_output.innerHTML="";
                    // Show "Please wait"
                    waiter.style.display = "block";
                }
                else if (e.data == "close") {
                    // Answer is complete
                    target_output.innerHTML="<hr><br/><b>Votre question :</b> <i>"+query+"</i>\n"+marked.parse(target_output.innerText.replace("<br/>", "\n"))+"<br/><hr>\n";
                    // Hide "Please Wait"
                    waiter.style.display = "none";
                    // Empty query field (previous context is memorized anyway)
                    query_input.value=""
                    // Close stream
                    answer_source.close();
                } else {
                    // Display new tokens
                    target_output.innerHTML +=e.data;
                    // Scroll to page bottom
                    window.scrollTo(0, document.body.scrollHeight);
                }
            };
        }
        function search(){
            // Display Patent search results
            var target_output = document.getElementById("response");
            var waiter = document.getElementById("waiter");
            // Clean history
            document.getElementById("history").innerHTML="";
            // Get query text
            query = document.getElementById("query").value
            const xhr = new XMLHttpRequest();
            // Show "Please Wait"
            waiter.style.display = "block";
            // Get search results
            xhr.open("GET", "/search?query="+encodeURIComponent(query), true);
            xhr.onload = (e) => {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    // Display search results
                    target_output.innerHTML=xhr.responseText;
                } else {
                    // If not ok : display error 
                    target_output.innerHTML=xhr.statusText;
                }
                // Hide "Please Wait"
                waiter.style.display = "none";
                document.getElementById("query").type="search"
            }
            };
            xhr.onerror = (e) => {
                // Display Error
                target_output.innerHTML=xhr.statusText;
                // Hide "Please Wait"
                waiter.style.display = "none";
                document.getElementById("query").type="search"
            };
            xhr.send(null);
        }
        function extend(){
            // Display UMLS concept search results
            var target_output = document.getElementById("response");
            var waiter = document.getElementById("waiter");
            // Clean history
            document.getElementById("history").innerHTML="";
            // Get query text
            query = document.getElementById("query").value
            const xhr = new XMLHttpRequest();
            // Show "Please Wait"
            waiter.style.display = "block";
            // Get search results
            xhr.open("GET", "/extend?query="+encodeURIComponent(query), true);
            xhr.onload = (e) => {
            if (xhr.readyState === 4) {
                if (xhr.status === 200) {
                    // Display search results
                    target_output.innerHTML=xhr.responseText;
                } else {
                    // If not ok : display error 
                    target_output.innerHTML=xhr.statusText;
                }
                // Hide "Please Wait"
                waiter.style.display = "none";
                document.getElementById("query").type="search"
            }
            };
            xhr.onerror = (e) => {
                // Display Error
                target_output.innerHTML=xhr.statusText;
                // Hide "Please Wait"
                waiter.style.display = "none";
            };
            xhr.send(null);
        }

        function append_query(concept) {
            // append concept IDs to query text
            var target_output = document.getElementById("query");
            if (concept.checked) {
                // add concept
                target_output.value+=" "+concept.id
            } else {
                // remove concept
                target_output.value=target_output.value.replace(" "+concept.id,"")
            }
        }

        function append_docs(doc) {
            // append doc ID to query text
            var target_output = document.getElementById("docs");
            if (concept.checked) {
                // add doc ID
                target_output.value+=" "+doc.id
            } else {
                // remove doc ID
                target_output.value=target_output.value.replace(" "+doc.id,"")
            }
        }

        function toggle_input(){
            input_id=document.getElementById("query");
            if (input_id.type == "search"){
                input_id.type = "file"
            }
            else {
                input_id.type = "search"
            }
        }

        function do_nothing(){
            return;
        }