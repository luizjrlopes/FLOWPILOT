export type User={id:string;name:string;role:"operator"|"approver"|"admin"|"auditor"};
export type Session={token:string;user:User};
export type Workflow={id:string;name:string;version:string;status:string;trigger:string;description:string;yaml:string;executions:number};
export type RunEvent={id:string;type:string;detail:string;level:string;metadata:Record<string,unknown>;created_at:string};
export type Run={id:string;workflow_id:string;state:string;trigger:string;actor:string;input:Record<string,any>;ai:Record<string,any>;result:Record<string,any>;current_step:number;retry:number;parent_run_id?:string;error?:string;created_at:string;updated_at:string;events:RunEvent[]};
