# TJPCore


## An API-based abstraction layer over TaskJuggler

## Pipelines:

### Generating reports:
 - #### (1) Fetching user sepecified project's data from elasticsearch.
 - #### (2) Wrapping data to OOP obejcts.
 - #### (3) Doing some manipulation and corrections over data objects.
 - #### (4) Generating a tjp file ( TaskJuggler project ) and defineing a project with data objects.
 - #### (5) Starting TaskJuggler engine ( tjp file compilation and generating reports as csv files ).
 - #### (6) Reading reports result from csv files into the python dictionaries and doing some manipulatio over it.
 - #### (Final) writing reports into the reports indexes in elasticsearch.

 <br><br>
#
 ### Scenario analyze:
  - #### Receive scenario specific data from user request.
  - #### other steps are the same as above, but except last one, instead of indexing scenario analyze reports, result will be return back as json stream to user.<br>it's like a normal request-response over http REST-API. 